import os
import subprocess
from typing import Iterable
from smolagents import tool

@tool
def is_gromacs_installed() -> bool:
  """Checks if Gromacs is installed.

  Returns:
    True if Gromacs is installed and its version can be retrieved, False otherwise.
  """
  try:
    # Attempt to execute the 'gmx' command with the '-version' option.
    # The 'capture_output=True' argument suppresses printing the output to the console
    # and captures it as a bytes object in the 'stdout' attribute.
    # The 'text=True' argument decodes the bytes object into a string.
    result = subprocess.run(['gmx', '-version'], capture_output=True, text=True, check=True)

    # Check if "GROMACS version" is present in the output (more robust check).
    return "GROMACS version" in result.stdout

  except FileNotFoundError:
    # Handle the case where the 'gmx' command is not found in the PATH.
    return False
  except subprocess.CalledProcessError:
    # Handle the case where the 'gmx' command exits with a non-zero status code (error).
    return False
  
@tool
def convert_pdb_to_gromacs(pdb_file: str, gro_file: str, workspace:str = ".") -> None:
    """Converts a PDB file to a GRO file using Gromacs' editconf tool.

    Args:
        pdb_file: Path to the input PDB file.
        gro_file: Path to the output GRO file.
        workspace: The directory where to save the converted file.

    Returns:
        True if the file has been successfully converted, False otherwise.
    """

    is_success = False
    try:
        subprocess.run(['gmx', 'editconf', '-f', pdb_file, '-o', os.path.join(workspace, gro_file), '-c'], check=True)
        print(f"Successfully converted {pdb_file} to {gro_file}")
        is_success = True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error converting PDB to GRO: {e}")
    finally:
        return is_success

@tool
def create_index_file(pdb_file: str, index_file: str, workspace:str = ".") -> bool:
    """Creates an index file for a given PDB file using Gromacs.

    Args:
        pdb_file: Path to the input PDB file.
        index_file: Name of the index file, without extension.
        workspace: The directory where to save the index file.

    Returns:
        True if the index files has been successfully created, False otherwise.
    """

    is_success = False
    try:
        ps = subprocess.Popen(('echo', 'q'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('gmx', 'make_ndx', '-f', pdb_file, 
                                          '-o', os.path.join(workspace, index_file+'.ndx')), stdin=ps.stdout)
        print(f"Successfully created index file: {index_file}")
        is_success = True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating index file: {e}")
    finally:
        return is_success

@tool
def prepare_system_files(pdb_file: str, output_prefix: str='', force_field: str='amber99sb-ildn', water_model:str = 'tip3p', workspace:str = ".") -> bool:
    """Prepares necessary files for a Gromacs simulation from a PDB file.

    Args:
        pdb_file: Path to the input PDB file.
        output_prefix: Prefix for the output files.
        force_field: The force field to use.
        water_model: The water model to use.
        workspace: The directory where to save any created or updated file.

    Returns:
      True if the simulation files have been successfully created, False otherwise.
    """
    workspace_abspath = os.path.abspath(workspace)
    sys_files_exist = workspace_contains_system_files(workspace_abspath, ['.gro', '.itp', '.top'])
    if sys_files_exist:
        return True
    else:
        if output_prefix == '':
            file_name_with_extension = os.path.basename(pdb_file)
            output_prefix, _ = os.path.splitext(file_name_with_extension)
        gro_file = f"{output_prefix}.gro"
        itp_file = f"{output_prefix}.itp"
        top_file = f"{output_prefix}.top"

        is_success = False
        try:
            subprocess.run(['gmx', 'pdb2gmx', '-f', pdb_file, 
                            '-o', os.path.join(workspace, gro_file), 
                            '-i', os.path.join(workspace, itp_file), 
                            '-p', os.path.join(workspace, top_file), 
                            '-ff', force_field, '-ignh', '-heavyh', '-water', water_model], check=True)
            print("Successfully prepared files for GMX.")
            is_success = True
        except FileNotFoundError:
            print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error preparing files: {e}")
        finally:
            return is_success
    
@tool
def prepare_and_solvate_box(gro_file: str, top_file: str, output_prefix: str, box_size: float = 1.0, workspace:str = ".") -> bool:
    """Prepares and solvates a simulation box using Gromacs.

    Args:
        gro_file: Path to the input GRO (.gro) file.
        top_file: Path to the input topology (.top) file.
        output_prefix: Prefix for the output files.
        box_size: The size of the box in nm. It must be at least 1.0.
        workspace: The directory where to save any created or updated file.

    Returns:
        True if the box preparation and solvation are successful, False otherwise.
    """

    solvated_gro_file = f"{output_prefix}_solv.gro"
    
    try:
      subprocess.run(['gmx', 'editconf', 
                      '-f', os.path.join(workspace, gro_file), 
                      '-o', os.path.join(workspace, solvated_gro_file), 
                      '-c', '-d', str(box_size), '-bt', 'cubic'], check=True)
      subprocess.run(['gmx', 'solvate', 
                      '-cp', os.path.join(workspace, solvated_gro_file), '-cs', 'spc216.gro', 
                      '-o', os.path.join(workspace, solvated_gro_file), 
                      '-p', os.path.join(workspace, top_file)], check=True)
      print(f"Successfully solvated the system. Output: {solvated_gro_file}")
      return True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error solvating the system: {e}")
        return False
    
@tool
def add_ions(gro_file: str, top_file: str, output_prefix: str, concentration: float = 0.15, workspace:str = ".") -> bool:
    """Adds ions to a solvated system using Gromacs.

    Args:
        gro_file: Path to the input GRO file.
        top_file: Path to the input topology file.
        output_prefix: Prefix for the output files.
        concentration: The desired ion concentration in M.
        workspace: The directory where to save any created or updated file.

    Returns:
        True if ion addition is successful, False otherwise.
    """

    ionized_gro_file = f"{output_prefix}_ionized.gro"
    is_success = False
    try:
        subprocess.run(['touch', os.path.join(workspace, 'ions.mdp')], check=True)
        subprocess.run(['gmx', 'grompp', '-f', os.path.join(workspace, 'ions.mdp'), 
                        '-c', os.path.join(workspace, gro_file), 
                        '-p', os.path.join(workspace, top_file), 
                        '-o', os.path.join(workspace, 'ions.tpr')], check=True)
        print("Successfully completed the grompp execution.")
        ps = subprocess.Popen(('echo', 'SOL'), stdout=subprocess.PIPE)
        output = subprocess.check_output(['gmx', 'genion', 
                                          '-s', os.path.join(workspace, 'ions.tpr'), 
                                          '-o', os.path.join(workspace, ionized_gro_file), 
                                          '-p', os.path.join(workspace, top_file), 
                                          '-neutral', '-conc', str(concentration)], stdin=ps.stdout)
        print(f"Successfully added ions. Output: {ionized_gro_file}")
        is_success = True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error adding ions: {e}")
    finally:
        return is_success
    
def workspace_contains_system_files(workspace: str, extensions: Iterable[str]):
   """
   Returns True if the `workspace` contains at least one file for every extension in `extensions`.
   Assumes dir_path contains only files and no subdirectories.

    Args:
      workspace: path to the directory to check.
      extensions: iterable of extension strings (with or without leading dot, case insensitive).

    Raises:
      NotADirectoryError if workspace is not a directory.
   """

   exts_needed = {('.' + e.lower().lstrip('.')) for e in extensions if e}
   if not os.path.isdir(workspace):
      raise NotADirectoryError(f"Not a directory: {workspace}")
   if not exts_needed:
      return True
   
   found = set()
   for name in os.listdir(workspace):
      full = os.path.join(workspace, name)
      if not os.path.isfile(full):
         continue
      _, extension = os.path.splitext(name)
      extension = extension.lower()
      if extension in exts_needed:
         found.add(extension)
         if found == exts_needed:
            return True
         
   return False
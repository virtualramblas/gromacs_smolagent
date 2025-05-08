import subprocess
from smolagents import tool

@tool
def is_gromacs_installed() -> bool:
  """Checks if Gromacs is installed and accessible in the system's PATH.

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
def convert_pdb_to_gromacs(pdb_file: str, gro_file: str) -> None:
    """Converts a PDB file to a GRO file using Gromacs' editconf tool.

    Args:
        pdb_file: Path to the input PDB file.
        gro_file: Path to the output GRO file.

    Returns:
        True if the file has been successfully converted, False otherwise.
    """

    is_success = False
    try:
        subprocess.run(['gmx', 'editconf', '-f', pdb_file, '-o', gro_file, '-c'], check=True)
        print(f"Successfully converted {pdb_file} to {gro_file}")
        is_success = True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error converting PDB to GRO: {e}")
    finally:
        return is_success

@tool
def create_index_file(pdb_file: str, index_file: str) -> None:
    """Creates an index file for a given PDB file using Gromacs.

    Args:
        pdb_file: Path to the input PDB file.
        index_file: Path to the output index file.

    Returns:
        True if the index files has been successfully created, False otherwise.
    """

    is_success = False
    try:
        ps = subprocess.Popen(('echo', '-e', '"q \n"'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('gmx', 'make_ndx', '-f', pdb_file, '-o', index_file+'.ndx'), stdin=ps.stdout)
        print(f"Successfully created index file: {index_file}")
        is_success = True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating index file: {e}")
    finally:
        return is_success

@tool
def prepare_simulation_files(pdb_file: str, output_prefix: str, force_field: str='amber99sb-ildn', water_model:str = 'tip3p') -> bool:
    """Prepares necessary files for a Gromacs simulation from a PDB file.

    Args:
        pdb_file: Path to the input PDB file.
        output_prefix: Prefix for the output files.
        force_field: The force field to use.
        water_model: The water model to use.

    Returns:
      True if the simulation files have been successfully created, False otherwise.
    """

    gro_file = f"{output_prefix}.gro"
    itp_file = f"{output_prefix}.itp"
    top_file = f"{output_prefix}.top"

    is_success = False
    try:
        subprocess.run(['gmx', 'pdb2gmx', '-f', pdb_file, '-o', gro_file, '-i', itp_file, '-p', top_file, '-ff', force_field, '-ignh', '-heavyh', '-water', water_model], check=True)
        print(f"Successfully prepared files for GMX.")
        is_success = True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error preparing files: {e}")
    finally:
        return is_success
    
@tool
def prepare_and_solvate_box(gro_file: str, top_file: str, output_prefix: str, box_size: float = 1.0) -> bool:
    """Prepares and solvates a simulation box using Gromacs.

    Args:
        gro_file: Path to the input GRO file.
        top_file: Path to the input topology file.
        output_prefix: Prefix for the output files.
        box_size: The size of the box in nm.

    Returns:
        True if the box preparation and solvation are successful, False otherwise.
    """

    solvated_gro_file = f"{output_prefix}_solv.gro"
    
    try:
      subprocess.run(['gmx', 'editconf', '-f', gro_file, '-o', solvated_gro_file, '-c', '-d', str(box_size), '-bt', 'cubic'], check=True)
      subprocess.run(['gmx', 'solvate', '-cp', solvated_gro_file, '-cs', 'spc216.gro', '-o', solvated_gro_file, '-p', top_file], check=True)
      print(f"Successfully solvated the system. Output: {solvated_gro_file}")
      return True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error solvating the system: {e}")
        return False
    
@tool
def add_ions(gro_file: str, top_file: str, output_prefix: str, concentration: float = 0.15) -> bool:
    """Adds ions to a solvated system using Gromacs.

    Args:
        gro_file: Path to the input GRO file.
        top_file: Path to the input topology file.
        output_prefix: Prefix for the output files.
        concentration: The desired ion concentration in M.

    Returns:
        True if ion addition is successful, False otherwise.
    """

    ionized_gro_file = f"{output_prefix}_ionized.gro"
    is_success = False
    try:
        subprocess.run(['touch', 'ions.mdp'], check=True)
        subprocess.run(['gmx', 'grompp', '-f', 'ions.mdp', '-c', gro_file, '-p', top_file, '-o', 'ions.tpr'], check=True)
        print("Successfully completed the grompp execution.")
        ps = subprocess.Popen(('echo', 'SOL'), stdout=subprocess.PIPE)
        output = subprocess.check_output(['gmx', 'genion', '-s', 'ions.tpr', '-o', ionized_gro_file, '-p', top_file, '-neutral', '-conc', str(concentration)], stdin=ps.stdout)
        print(f"Successfully added ions. Output: {ionized_gro_file}")
        is_success = True
    except FileNotFoundError:
        print("Error: 'gmx' command not found. Make sure Gromacs is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error adding ions: {e}")
    finally:
        return is_success
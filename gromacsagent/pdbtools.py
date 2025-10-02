import os
from Bio.PDB import *
from smolagents import tool

@tool
def is_pdb_valid(pdb_file: str) -> bool:
    """Checks if a PDB file has a valid structure or not.

    Args:
        pdb_file: Full name of the input PDB file.

    Returns:
        True if the passed PDB file has a valid structure, False otherwise.
    """
    is_valid_pdb = False

    file_prefix = 'file://'
    if pdb_file.startswith(file_prefix):
        pdb_file = pdb_file.split(file_prefix)[1]

    file_name_with_extension = os.path.basename(pdb_file)
    file_name, _ = os.path.splitext(file_name_with_extension)
    parser = PDBParser()
    try:
        parser.get_structure(file_name, pdb_file)
        is_valid_pdb = True
    except:
        print("The provided PDB file has an invalid structure.")

    return is_valid_pdb

@tool
def download_from_protein_data_bank(structure_id:str, workspace:str = ".") -> bool:
    """Download a protein structure in PDB format from the Protein Data Bank.

    Args:
        structure_id: The ID of the protein structure to download.
        workspace: The directory where to save the downloaded PDB file.

    Returns:
        True if the download is successful, False otherwise.
    """
    has_file_been_downloaded = False

    try:
        pdbl = PDBList()
        pdbl.retrieve_pdb_file(structure_id, 
                            pdir=str(os.path.abspath(workspace)), 
                            file_format="pdb", 
                            overwrite=True)
        os.rename("pdb" + structure_id + ".ent", structure_id + ".pdb")
        has_file_been_downloaded = True
    except:
        print(f"Failed to download the {structure_id} PDB file")

    return has_file_been_downloaded

@tool
def remove_water_molecules(pdb_file: str, workspace:str = ".") -> bool:
    """Remove water molecules from a PDB file.

    Args:
        pdb_file: The name of the input PDB file.
        workspace: The directory where to find the input PDB file.

    Returns:
        True if the water molecules have been successfully removed, False otherwise.
    """
    is_water_removed = False

    workspace_absolute_path = os.path.abspath(workspace)
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein", os.path.join(workspace_absolute_path, pdb_file))

    for model in structure:
        for chain in list(model):
            for residue in list(chain):
                if residue.get_resname() == "HOH":
                    chain.detach_child(residue.id)
                  
    # Save the cleaned structure
    io = PDBIO()
    io.set_structure(structure)
    output_file = os.path.join(workspace_absolute_path, pdb_file)
    io.save(output_file)
    is_water_removed = True

    return is_water_removed

@tool
def analyze_pdb_file(pdb_file: str) -> tuple[list, list, list]:
    """Perform analysis of a PDB file.

    Args:
        pdb_file: Path to the input PDB file.

    Returns:
        Lists of the chains, residues and atoms present in the input PDB file structure.
    """
    print('-----> pdb_file = ' + pdb_file)
    file_name_with_extension = os.path.basename(pdb_file)
    file_name, extension = os.path.splitext(file_name_with_extension)
    parser = PDBParser()
    structure = parser.get_structure(file_name, pdb_file)
    chain_list = [chain for chain in structure.get_chains()]
    residue_list = [residue for residue in structure.get_residues()]
    atom_list = [atom for atom in structure.get_atoms()]

    return chain_list, residue_list, atom_list
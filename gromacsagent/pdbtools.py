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
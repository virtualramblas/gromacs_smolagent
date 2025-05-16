import os
import subprocess
import matplotlib.pyplot as plt
from smolagents import tool

emp_default_values = """
include                  =
define                   =
integrator               = steep
dt                       = 0.001
nsteps                   = 1000
init_step                = 0
simulation_part          = 1
comm-mode                = Linear
nstcomm                  = 1
comm-grps                = system

emtol                    = 1000
emstep                   = 0.01
niter                    = 20
fcstep                   = 0
nstcgsteep               = 1000
nbfgscorr                = 10

nstxout                  = 10
nstvout                  = 0
nstfout                  = 0
nstlog                   = 10
nstcalcenergy            = 10
nstenergy                = 10
nstxtcout                = 10

cutoff-scheme            = Verlet
nstlist                  = 20
ns-type                  = Grid
pbc                      = xyz
rlist                    = 1.0
coulombtype              = pme
coulomb-modifier         = Potential-shift-Verlet
rcoulomb-switch          = 1.0
rcoulomb                 = 1.0
vdw-type                 = cut-off
vdw-modifier             = Potential-shift-Verlet
rvdw-switch              = 1.0
rvdw                     = 1.0


constraints              = none
constraint-algorithm     = Lincs
"""

@tool
def gromacs_energy_minimization(workspace_dir: str, prefix: str='em') -> str:
  """
  Performs energy minimization using Gromacs within a specified workspace directory.

  Args:
    workspace_dir: The path to the workspace directory containing the simulation files.
    prefix: The prefix for all the files that will be generated following execution of the code in this function.

  Returns:
    A string indicating the outcome of the energy minimization process.
  """

  gro_file = None
  top_file = None
  mdp_file = None
  for fname in os.listdir(workspace_dir):
    if fname.endswith("_ionized.gro"):
      gro_file = fname
    elif fname.endswith(".top"):
      top_file = fname
    elif fname.endswith(prefix+".mdp"):
      mdp_file = fname

  if not gro_file or not top_file:
    return "Error: A .gro and .top file must exist in the workspace directory for energy minimization."

  try:
    os.chdir(workspace_dir)

    # Create ions file if it doesn't exist and populate it with default values
    if mdp_file is None:
      mdp_file = prefix + '.mdp'
      subprocess.run(["touch", mdp_file], check=True)
      with open(mdp_file, "w") as f:
        f.write(emp_default_values)

    # Create the .tpr file for energy minimization
    subprocess.run(["gmx", "grompp", "-f", mdp_file, "-c", gro_file, "-p", top_file, "-o", prefix + '.tpr'], check=True)

    # Run energy minimization
    subprocess.run(["gmx", "mdrun", "-v", "-deffnm", prefix], check=True)

    return f"Energy minimization completed successfully. Output files ({prefix}.log, {prefix}.edr, {prefix}.gro, etc.) should be in the workspace directory."

  except subprocess.CalledProcessError as e:
    return f"Error during Gromacs execution: {e}"
  except FileNotFoundError as e:
    return f"Error: Gromacs command not found. Is Gromacs installed and in your PATH? {e}"
  except Exception as e:
    return f"An unexpected error occurred: {e}"
  
@tool
def plot_edr_to_png(workspace_dir: str, output_prefix: str) -> str:
  """
  Starting from an .edr file from Gromacs, generates an .xvg file, and plots
  a chosen energy property to a PNG image.

  Args:
    workspace_dir: The path to the input .edr file.
    output_prefix: Prefix for the output .xvg and .png files.

  Returns:
    A string indicating the outcome of the analysis.
  """

  edr_file = None
  for fname in os.listdir(workspace_dir):
    if fname.endswith(".edr"):
      edr_file = fname

  if not edr_file:
    return "Error: A .edr file must exist in the workspace directory."

  xvg_file = f"{output_prefix}.xvg"
  png_file = f"{output_prefix}.png"

  try:
    os.chdir(workspace_dir)
    # Generate the .xvg file from the .edr file
    process = subprocess.Popen(['gmx', 'energy', '-f', edr_file, '-o', xvg_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=b"Potential\n") # Select Potential energy
    if process.returncode != 0:
        print(f"Error generating XVG file: {stderr.decode()}")
        return

    print(f"Successfully generated {xvg_file}")

    # Read the .xvg file and plot the data.
    # XVG files often have comments at the beginning starting with '@' or '#'
    # We skip these lines.
    data = []
    with open(xvg_file, 'r') as f:
        for line in f:
            if not line.startswith(('@', '#')):
                try:
                    time, energy = map(float, line.split())
                    data.append((time, energy))
                except ValueError:
                    # Skip lines that don't contain numerical data in expected format
                    pass

    if not data:
        return f"No plottable data found in {xvg_file}"

    times = [d[0] for d in data]
    energies = [d[1] for d in data]

    plt.figure(figsize=(10, 6))
    plt.plot(times, energies)
    plt.xlabel('Time (ps)') 
    plt.ylabel('Potential Energy (kJ/mol)') 
    plt.title('Potential Energy over Time')
    plt.grid(True)
    plt.savefig(png_file)
    plt.close()

    return f"Successfully generated plot {png_file}"
  except FileNotFoundError:
    return "Error: 'gmx' command or matplotlib not found. Make sure they are installed and in your PATH."
  except Exception as e:
    return f"An unexpected error occurred: {e}"
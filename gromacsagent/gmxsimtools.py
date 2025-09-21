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
def gromacs_energy_minimization(prefix: str='em', workspace: str=".") -> str:
  """
  Performs energy minimization using Gromacs within a specified workspace directory.

  Args:
    workspace: The directory containing the simulation files.
    prefix: The prefix for all the files that will be generated following execution of the code in this function.

  Returns:
    A string indicating the outcome of the energy minimization process.
  """

  gro_file = None
  top_file = None
  mdp_file = None
  workspace = os.path.abspath(workspace)
  for fname in os.listdir(workspace):
    if fname.endswith("_ionized.gro") or fname.endswith(".gro"):
      gro_file = fname
    elif fname.endswith(".top"):
      top_file = fname
    elif fname.endswith(prefix+".mdp"):
      mdp_file = fname

  if not gro_file or not top_file:
    return "Error: A .gro and .top file must exist in the workspace directory for energy minimization."

  try:
    os.chdir(workspace)

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
def plot_edr_to_png(workspace: str, output_prefix: str) -> str:
  """
  Starting from an .edr file from Gromacs, generates an .xvg file, and plots
  a chosen energy property to a PNG image.

  Args:
    workspace: The path to the input .edr file.
    output_prefix: Prefix for the output .xvg and .png files.

  Returns:
    A string indicating the outcome of the analysis.
  """

  edr_file = None
  for fname in os.listdir(workspace):
    if fname.endswith(".edr"):
      edr_file = fname

  if not edr_file:
    return "Error: A .edr file must exist in the workspace directory."

  xvg_file = f"{output_prefix}.xvg"
  png_file = f"{output_prefix}.png"

  try:
    os.chdir(workspace)
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
  
@tool
def gromacs_equilibration(workspace: str, prefix: str = 'nvt', temperature: float = 300) -> str:
  """
  Performs equilibration (e.g., NVT) using Gromacs within a specified workspace directory.

  Args:
    workspace: The path to the workspace directory containing the simulation files.
    prefix: The prefix for the output files (e.g., 'nvt' for NVT equilibration).
    temperature: The target temperature for equilibration in Kelvin.

  Returns:
    A string indicating the outcome of the equilibration process.
  """

  gro_file = None
  top_file = None
  mdp_file = None

  try:
    for fname in os.listdir(workspace):
        if fname.endswith("_ionized.gro"):
            gro_file = fname 
        elif fname.endswith(".top"):
            top_file = fname 
        elif fname.endswith(f"{prefix}.mdp"):
            mdp_file = fname 

    if gro_file is None or top_file is None:
        return "Error: A .gro and .top file must exist in the workspace directory."

    # Navigate to the workspace directory
    os.chdir(workspace)

    if mdp_file is None:
        # Create an equilibration .mdp file
        mdp_file = f"{prefix}.mdp"
        # Use basic NVT parameters
        nvt_mdp_content = f"""
    title                    = {prefix} equilibration
    integrator               = md        ; leap-frog integrator
    dt                       = 0.002     ; 2 fs
    nsteps                   = 50000     ; 2 fs * 50000 = 100 ps
    nstxout                  = 500       ; save coordinates every 1 ps
    nstvout                  = 500       ; save velocities every 1 ps
    nstenergy                = 500       ; save energies every 1 ps
    nstlog                   = 500       ; update log file every 1 ps
    cutoff-scheme            = Verlet
    nstlist                  = 20
    ns-type                  = Grid
    pbc                      = xyz
    rlist                    = 1.0
    coulombtype              = pme
    coulomb-modifier         = Potential-shift-Verlet
    rcoulomb-switch          = 0
    rcoulomb                 = 1.0
    vdw-type                 = cut-off
    vdw-modifier             = Potential-shift-Verlet
    rvdw-switch              = 0
    rvdw                     = 1.0
    constraints              = h-bonds    ; constrain all bonds (e.g., with LINCS)
    constraint-algorithm     = Lincs
    continuation             = no         ; not a continuation of previous simulation
    lincs-iter               = 1          ; do 1 iteration of LINCS
    lincs-order              = 4          ; highest order in the expansion of the contraint coupling matrix
    tcoupl                   = V-rescale  ; Nose-Hoover, Berendsen
    tc-grps                  = system    ; groups to couple to separate thermostats
    tau_t                    = 0.1       ; [ps] time constant for coupling
    ref_t                    = {temperature}  ; [K] reference temperature
    pcoupl                   = no         ; no pressure coupling in NVT
    gen_vel                  = yes        ; assign velocities from Maxwell distribution
    gen_temp                 = {temperature}  ; [K] temperature for Maxwell distribution
    gen_seed                 = -1         ; generate a random seed
    """
        with open(mdp_file, 'w') as f:
          f.write(nvt_mdp_content)

    # Create the .tpr file for equilibration
    subprocess.run(["gmx", "grompp", "-f", mdp_file, "-c", gro_file, "-p", top_file, "-o", f"{prefix}.tpr"], check=True)

    # Run the equilibration simulation
    subprocess.run(["gmx", "mdrun", "-v", "-deffnm", prefix], check=True)

    return f"Equilibration ({prefix}) completed successfully. Output files ({prefix}.log, {prefix}.edr, {prefix}.xtc, etc.) should be in the workspace directory."

  except subprocess.CalledProcessError as e:
    return f"Error during Gromacs execution: {e}"
  except FileNotFoundError as e:
    return f"Error: Gromacs command not found. Is Gromacs installed and in your PATH? {e}"
  except Exception as e:
    return f"An unexpected error occurred: {e}"
  
   
import ifcopenshell
from tkinter import Tk, filedialog
print("----------------------------------------------")
print("Hello, thank you for trying out our tool. \n The tool is made for assessing GWP for different materials' used in exterior walls. \n You will now be guided through the different steps. ")
print("----------------------------------------------")

# The user can select an IFC file
def select_ifc_file():
    # Hide the main tkinter window
    root = Tk()
    root.withdraw()

    print("Please choose the IFC file you want to use")
    file_path = filedialog.askopenfilename(
        title="Select IFC file",
        filetypes=[("IFC files", "*.ifc"), ("All files", "*.*")]
    )

    # Output, if the IFC file is not found
    if not file_path:
        raise FileNotFoundError("No IFC file selected. Please run again and choose a file.")

    print(f"\n Please wait, while the different exterior wall types are listed for your chosen IFC file :\n{file_path}\n")
    print("----------------------------------------------")
    return file_path

# The loaded IFC file can now be loaded into another part of the code
ifc_path = select_ifc_file()
ifc_file = ifcopenshell.open(ifc_path)
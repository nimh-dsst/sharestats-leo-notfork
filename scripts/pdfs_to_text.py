import os
import subprocess
import multiprocessing
import shutil  # Import shutil for copying files

input_folder = "delme_data/pdfs"  # Input folder path
output_folder = "delme_data/txts"  # Output folder path
warnings_file = "delme_data/pdfs_to_text_error.txt"  # Store PDFs with warnings

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)


def convert_pdf_to_text(pdf_file):
    pdf_path = os.path.join(input_folder, pdf_file)
    txt_file = os.path.splitext(pdf_file)[0] + ".txt"
    txt_path = os.path.join(output_folder, txt_file)

    try:
        subprocess.run(
            ["pdftotext", pdf_path, txt_path],
            check=True,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"Successfully converted {pdf_file} to {txt_file}")
    except subprocess.CalledProcessError as e:
        warning_message = e.stderr
        with open(warnings_file, "a") as wf:
            wf.write(f"{pdf_file}: {warning_message}\n")


if __name__ == "__main__":
    pdf_files = [
        pdf_file
        for pdf_file in os.listdir(input_folder)
        if pdf_file.endswith(".pdf")
    ]

    # Copy txt files from input_folder to output_folder
    for txt_file in os.listdir(input_folder):
        if txt_file.endswith(".txt"):
            txt_src_path = os.path.join(input_folder, txt_file)
            txt_dest_path = os.path.join(output_folder, txt_file)
            shutil.copy(txt_src_path, txt_dest_path)
            print(f"Successfully copied {txt_file} to {output_folder}")

    # Pool of worker processes for PDF conversion
    num_processes = multiprocessing.cpu_count()  # or set it manually
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(convert_pdf_to_text, pdf_files)

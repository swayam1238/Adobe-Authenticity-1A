# Adobe-Authenticity-1A
# Round 1A: Understand Your Document - Adobe Hackathon

This repository contains the solution for Round 1A of the Adobe "Connecting the Dots" Hackathon. The script is designed to intelligently parse PDF documents to extract a structured outline, identifying the document's title and its hierarchical headings (H1, H2, H3).

The solution is built to be robust, handling a variety of PDF layouts and internal structures, including those with "dirty" or poorly encoded text.

---

## 🚀 How to Build and Run

*Prerequisites:* You must have Docker installed and running on your system (Linux, macOS, or Windows with WSL2).

### Step 1: Add Input PDFs

Place all the PDF files you wish to process into the input/ directory within this folder (Challenge-1/A/). The script is designed to automatically find and process every .pdf file in this directory.

### Step 2: Build the Docker Image

Navigate to this directory (Challenge-1/A/) in your terminal and execute the following command. This command builds a self-contained Docker image named round1a-solution that includes all necessary dependencies.

bash
docker build --platform linux/amd64 -t round1a-solution .


### Step 3: Run the Solution

Once the image is built, run the following command. This will start the container, mount your local input and output folders, and execute the analysis in an isolated environment with no network access, as per the hackathon rules.

bash
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none round1a-solution


### Step 4: Check the Output

After the container finishes its execution, the output/ directory will be populated with JSON files. For each filename.pdf in the input folder, a corresponding filename.json will be generated, containing the extracted title and outline.

---

## 🛠 Technical Approach

This solution employs a resilient, multi-pass heuristic approach to accurately parse PDF structures. It is designed to overcome common challenges like complex layouts, inconsistent formatting, and poor text encoding.

### 1. Multi-Source Structure Detection

The script does not rely on a single method. It intelligently prioritizes the most reliable sources of information first:

-   *Built-in Table of Contents (TOC):* The script first attempts to read the PDF's embedded TOC. If a high-quality TOC is present, it is used as the primary source for the outline, as this is the most explicit representation of the author's intended structure.

-   *Visual Heuristic Analysis:* If the TOC is absent or insufficient, the script falls back to a sophisticated visual analysis of the document's pages.

### 2. Defensive Text and Style Analysis

To handle real-world "dirty" PDFs, several defensive layers are implemented:

-   *Gibberish Detection:* A custom function identifies and discards text that appears to be a result of poor text extraction (e.g., garbled characters, excessive spacing), preventing it from polluting the final output.

-   *Header/Footer Exclusion:* The script defines exclusion zones at the top (10%) and bottom (10%) of each page. Any text falling within these zones (commonly headers, footers, and page numbers) is ignored during the heading analysis.

-   *Robust Title Finding:* The title is identified by finding the text with the largest font size on the first page. This is more reliable than relying on potentially incorrect or missing file metadata.

### 3. Dynamic Heading Classification

The core of the visual analysis is a dynamic classification engine:

-   *Style Profiling:* The script first analyzes the entire document to create a profile of its font styles, considering both *font size* and *font weight (boldness)*. The most common style is designated as the "body text."

-   *Candidate Identification:* It then identifies all lines of text that are stylistically more prominent than the body text (e.g., larger, bolder, or both). These become "potential headings."

-   *Hierarchical Mapping:* Finally, it analyzes the unique styles of only these potential headings. The top 3 most significant styles are dynamically mapped to H1, H2, and H3, ensuring the final outline accurately reflects the document's visual and logical hierarchy. This method adapts to each document's specific styling rather than using fixed rules.

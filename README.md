# EOL Scanner

![GitHub](https://img.shields.io/github/license/hariprasadpo28/eol-scanner)
![GitHub last commit](https://img.shields.io/github/last-commit/hariprasadpo28/eol-scanner)
![GitHub issues](https://img.shields.io/github/issues-raw/hariprasadpo28/eol-scanner)
![GitHub pull requests](https://img.shields.io/github/issues-pr/hariprasadpo28/eol-scanner)

Identify and mark End-of-Life (EOL) programming languages present in Docker images with this EOL Scanner.

## Prerequisites

Before running the EOL Scanner, ensure the following prerequisites are met:

- [Docker](https://www.docker.com/) is installed on your system.
- [Syft](https://github.com/anchore/syft) is installed. You can install Syft using the following command:

# Usage

### Clone the repository
```
git clone https://github.com/hariprasadpo28/eol-scanner.git
```

### Change into the project directory:
```
cd eol-scanner/
```

### Run the EOL Scanner with the desired docker image
```
python3 main.py <docker-image-with-tag>
```

### View the results:
  The EOL Scanner will analyze the Docker images and mark any EOL programming languages.
  Review the generated reports or logs for detailed information.

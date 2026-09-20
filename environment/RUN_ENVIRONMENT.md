# Recorded run environment

## Hardware

- GPU: one NVIDIA GeForce RTX 3090, 24,576 MiB
- GPU driver: 595.71.05
- CPU allocation: 15 Intel Xeon Platinum 8358P cores
- RAM: 90 GB
- system disk: 30 GB
- expandable data disk: 50 GB at start

The three language-model controls ran sequentially. Their measured peak CUDA
allocations were 7.87 GiB (Qwen), 7.45 GiB (Phi), and 13.91 GiB (Mistral).
IWCC itself and all released-record analyses are CPU-only.

## Software

- Ubuntu Linux (AutoDL image)
- Python 3.12.3
- PyTorch 2.8.0+cu128
- CUDA runtime 12.8
- transformers 4.57.6
- accelerate 1.14.0
- ALFWorld 0.4.2
- TextWorld 1.7.0
- ScienceWorld 1.2.3
- OpenJDK 17.0.20
- NumPy 2.3.2
- Matplotlib 3.10.5
- pytest 8.4.2

Model repository names and immutable revisions are recorded in
`configs/models.json`. The experiment does not rely on Docker.

## Storage

The paper folder, including released trajectories, predictions, dependency
snapshot, and both PDFs, is below 25 MB before packaging. Model caches require
roughly 35--50 GB depending on Hugging Face cache deduplication. ALFWorld data,
Python environments, and temporary files should be placed on the data disk;
the 30 GB system disk should contain only the operating system and small tools.

## Paper build

The manuscript requires XeLaTeX, `latexmk`, BibTeX, Noto CJK fonts, and the
Chinese TeX language collection. On Ubuntu 22.04 the relevant system packages
are `texlive-xetex`, `texlive-latex-extra`, `texlive-lang-chinese`,
`fonts-noto-cjk`, and `latexmk`.

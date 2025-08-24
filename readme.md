Face Registration and Recognition API Service
===
Cornerstone: TDG Cao Tran Duy

## Purpose of the repo:
this repository contains backbone code for Face Registration and Recognition API Service, implemented into our group's *small* check-in, check-out application system project

## Requirement:
project was developed to run on *NVIDIA GTX 1650*

## Prerequisite:
>dlib 19.24.2 (or later)
* Instruction:

0. **check if your device support CUDA**
    
1. Install:
- [cmake 3.20](https://cmake.org/files/v3.20/) 
- visual build tool 16 2019
* **if your device support CUDA**
    - [cuda 12.6](https://developer.nvidia.com/cuda-toolkit-archive)
    - [cuDNN](https://developer.nvidia.com/cudnn-9-1-0-download-archive)
2. Copy (**if your device support CUDA. if not, go to step 4**)
    - copy all of the .dll files inside of CUDNN bin directory (e.g., `C:\Program Files\NVIDIA\CUDNN\v9.1\bin\12.4`) into CUDA bin directory (e.g., `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin`).

    - copy all of the files inside of CUDNN include directory (e.g., `C:\Program Files\NVIDIA\CUDNN\v9.1\include\12.4`) and paste into CUDA's include directory (e.g., `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\include`)

    - copy all of the files inside of CUDNN lib x64 directory (e.g., `C:\Program Files\NVIDIA\CUDNN\v9.1\lib\12.4\x64`) into CUDA's lib x64 directory (e.g., `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\lib\x64`)
3. **Optional**: make sure environment path is set in ``%PATH%``. To check, go to `Control Panel\System and Security\System\Advanced system settings\Environment Variables`
4. **Set environment path for CMake:**
    - Find the directory where CMake is installed (e.g., `C:\Program Files\CMake\bin`).
    - Open `Control Panel\System and Security\System\Advanced system settings\Environment Variables`.
    - Under "System variables", select `Path` and click "Edit".
    - Click "New" and add the CMake `bin` directory path.
    - Click "OK" to save changes.

5. Install dlib using pip: Run this command in terminal 
```bash
pip install dlib
```
- **or after finishing step 4, you can go straight to the next instruction**


# Note: 
you can initialize virtual environment by command 
```bash
python -m venv <folder_name_of_the_virtual_environment>
```
by this you will have a safe environment to install packages (note to KIET, please add the venv folder to .gitignore)

run ``pip install -r requirements.txt`` in terminal.

for document on how to use api, go to localhost:<your_port>/docs 

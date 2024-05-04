# JFT (Json File Formatter)

## General Info
JFT (Json File Formatter) is a project that makes it easy to splice long format JSON files together.

## Setup
To run this project, you need Python 3 installed on your system.

Check if Python 3 is already installed:
```bash
python3 --version

```
You will see an output similar to this if already installed: ```Python 3.x.x```

If you **don't see** this output, you need to install Python from [here](https://www.python.org/downloads/)

**Installation guides**
[Windows 10](https://www.youtube.com/watch?v=MHJ5k-MARUk)
[MacOS](https://www.youtube.com/watch?v=nhv82tvFfkM)
[Linux](https://www.youtube.com/watch?v=IAco2SSuGms)

**Tips for Windows Users**:
If you are using Windows, it's easier to install Python from the Windows App Store. You can find Python by searching for "Python" in the store.


## Usage Tips

You need a command prompt to run the tool. 

1. **Collect JSON files into a folder.**
   
2. **Then, write the path of this folder to the config file on the command line.**

3. **To work cleaner, rename the files.**

4. **You need to determine the file you will add. (This will usually be file #1)**

5. **By default, when you specify the new file name, it backs up the first file. If you want to backup any file you want, you know the command to use.**

6. **There are multiple ways to add, you can try whichever is easier for you and suits your work.**



## Examples

### Processing JSON Files in a Working Folder

To process JSON files in a specific folder, use the `-f` flag followed by the folder path:
```bash
python3 jft.py -f $PATH

```


### Rename and Sorting JSON Files Arithmetically

To sort each of the files arithmetically, use the `-r` flag:
```bash
python3 jft.py -r PEPE

```

### Determining the Main File and Taking Its Backup

To determine the first file (the main file to which JSON files will be added) and take its backup by default, use the `-s` flag:
```bash
python3 jft.py -s PEPE1.json

```


### Backup JSON file

To take the backup of a specified file, use the `-b` flag:

```bash
python3 jft.py -b PEPEx.json

```
 
### Adding File Data to the Main File

To add the file data named PEPE2.json to the main file, use the `-a` flag:

```bash
python3 jft.py -a PEPE2.json

```


### Append File Data to the Main File Multiple Times

To append the file named PEPE2.json to the main file 5 times, use the `-a` flag followed by the `-c` flag and the number of times:

```bash
python3 jft.py -a PEPE2.json -c 5

```



### Adding Multiple Files Sequentially

To add PEPE2.json and PEPE3.json 5 times sequentially, use the `-m` flag followed by the file names and the `-c` flag:

```bash
python3 jft.py -m PEPE2.json PEPE3.json -c 3

```


### Adding Files Specified by Range

Instead of typing each file name, you can specify a range using two integers, and all PEPEx.json files in between are added to the main file. (The `-c` parameter can also be used here):

```bash
python3 jft.py -R  2-3 -c 3

```


### Peppening Art

```bash
python3 jft.py -p

```

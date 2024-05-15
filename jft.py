import argparse
import os
import json
import shutil

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file) and os.path.getsize(self.config_file) > 0:
            with open(self.config_file, 'r') as f:
                try:
                    config = json.load(f)
                    return config
                except json.JSONDecodeError:
                    print("Error: Invalid JSON structure in config file. Using default configuration.")
        return {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def backup_file(self, file_name):
        work_folder = self.get("work_folder","")
        file_path = os.path.join(work_folder, file_name)
        backup_path = file_path + ".bak"
        try:
            shutil.copyfile(file_path, backup_path)
            print(f"Backup created for file '{file_name}': {backup_path}")
            return backup_path
        except FileNotFoundError:
            print(f"Error: File '{file_name}' not found.")
            return None
        except Exception as e:
            print(f"Error creating backup for file '{file_name}': {e}")
            return None

    def rename_json_files(self, new_name):
        work_folder = self.get("work_folder", "")
        if not work_folder:
            print("Error: Working folder is not specified.")
            return

        files = os.listdir(work_folder)
        json_files = [file for file in files if file.endswith('.json')]
        
        json_files_sorted = sorted(json_files, key=lambda x: int(x.split('(')[1].split(')')[0]) if '(' in x and ')' in x else 0)

        file_map = {}
        for i, file_name in enumerate(json_files_sorted, start=1):
            _, file_extension = os.path.splitext(file_name)
            new_file_name = f"{new_name}{i}{file_extension}"
            file_map[file_name] = new_file_name
        
        for file_name in json_files:
            old_file_path = os.path.join(work_folder, file_name)
            new_file_name = file_map[file_name]
            new_file_path = os.path.join(work_folder, new_file_name)
            os.rename(old_file_path, new_file_path)
            print(f"{file_name} -> {new_file_name}")

        self.config['new_name'] = new_name
        self.save_config()

    def specify_work_file(self, first_file):
        work_folder = self.get("work_folder", "")
        if not work_folder:
            print("Error: Working folder is not specified.")
            return False
        
        files = os.listdir(work_folder)
        json_files = [file for file in files if file.endswith('.json')]
        
        if first_file not in json_files:
            print(f"Error: The work file '{first_file}' does not exist.")
            return False
        
        file_path = os.path.join(work_folder, first_file)
        backup_path = self.backup_file(file_path)
        if not backup_path or not file_path:
            return False
        
        self.config["first_file"] = first_file
        self.save_config()
        
        print("Work-file specified:", first_file)
        return True

    def append_single_json_to_file(self, json_file, count=1):
        first_file = self.get("first_file", "")
        work_folder = self.get("work_folder", "")

        target_file = os.path.join(work_folder, first_file)
        
        try:
            with open(target_file, 'r') as f:
                target_content = json.load(f)
        except FileNotFoundError:
            print(f"Error: Target file '{target_file}' not found.")
            return
        except json.JSONDecodeError:
            print(f"Error: Unable to decode JSON content in target file '{target_file}'.")
            return

        json_file_path = os.path.join(work_folder, json_file) 

        try:
            with open(json_file_path, 'r') as f:
                json_content = json.load(f)
        except FileNotFoundError:
            print(f"Error: JSON file '{json_file}' not found.")
            return
        except json.JSONDecodeError:
            print(f"Error: Unable to decode JSON content in file '{json_file}'.")
            return
        
        for _ in range(count):
            target_content.append(json_content[0])
        
        try:
            with open(target_file, 'w') as f:
                json.dump(target_content, f, indent=4)
            print(f"Successfully appended JSON file '{json_file}' to '{target_file}'.")
        except Exception as e:
            print(f"Error: Unable to write to target file '{target_file}': {e}")


    def append_multiple_json_to_file(self, *args, count=1):
        first_file = self.get("first_file", "")
        work_folder = self.get("work_folder", "")

        target_file = os.path.join(work_folder, first_file)
        
        try:
            with open(target_file, 'r') as f:
                target_content = json.load(f)
        except FileNotFoundError:
            print(f"Error: Target file '{target_file}' not found.")
            return
        except json.JSONDecodeError:
            print(f"Error: Unable to decode JSON content in target file '{target_file}'.")
            return
        
        for json_file in args:
            json_file_path = os.path.join(work_folder, json_file) 
            try:
                with open(json_file_path, 'r') as f:
                    json_content = json.load(f)
            except  FileNotFoundError:
                print(f"Error: JSON file '{json_file}' not found.")
                return
            except json.JSONDecodeError:
                print(f"Error: Unable to decode JSON content in file '{json_file}'.")
                return

            for _ in range(count):
                target_content.append(json_content[0])

        try:
            with open(target_file, 'w') as f:
                json.dump(target_content, f, indent=4)
            print(f"Successfully appended {len(args)} JSON files to '{target_file}' {count} times.")
        except Exception as e:
            print(f"Error: Unable to write to target file '{target_file}': {e}")


    def append_files_between_range(self, first_file, last_file, count=1):
        work_folder = self.get("work_folder", "")
        file_name = self.get("new_name", "")

        if not first_file.isdigit() or not last_file.isdigit():
            print("Error: Both arguments in the range should contain numerical values.")
            return

        file_number1 = int(first_file)
        file_number2 = int(last_file)

        for number in range(file_number1, file_number2 + 1):
            real_file = f"{file_name}{number}.json"
            self.append_single_json_to_file(os.path.join(work_folder, real_file), count)


def print_ascii_pepe(ascii_file=os.path.join(os.getcwd(),"pepe.txt")):
    try:
        with open(ascii_file, "r") as f:
            ascii_art = f.read()
            print(ascii_art)
    except FileNotFoundError:
        print("Error: ASCII art file not found.")


if __name__=="__main__":

    config_manager = ConfigManager()

    parser = argparse.ArgumentParser(description="", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-f', "--folder", metavar="FOLDER", type=str, help="specify the work folder")
    
    parser.add_argument('-s', "--specify", metavar="MAIN_FILE", type=str, help="determines the first file")
    parser.add_argument("-a","--append",type=str, metavar="SOURCE_FILE", help="appends a json file to the end of the target file")
    parser.add_argument("-c", "--count", type=int, metavar="NUMBER", default=1, help="number of times to append the source content to the target file. Default is 1.")
    parser.add_argument("-r", "--rename", type=str, help="renames a file sequentially and with a custom name")
    parser.add_argument('-m', "--multiple", nargs='+', type=str, help="selects multiple files (use with other parameters -a)")
    parser.add_argument("-b", "--backup", metavar="FILE", type=str,  help="takes a backup of the file.")
    parser.add_argument("-R", "--range", metavar="NUMBER1-NUMBER2", type=str,  help="specifies the range of files to process. Format: start-end.")
    parser.add_argument("-P", "--pepe", action="store_true", help="Peppening")

    args = parser.parse_args()

    if args.folder:
        config_manager.set("work_folder", args.folder)
    elif args.rename:
        config_manager.rename_json_files(args.rename)
    elif args.specify:
        config_manager.specify_work_file(args.specify)
    elif args.append and args.count:
        config_manager.append_single_json_to_file(args.append, args.count)
    elif args.multiple and args.count:
        config_manager.append_multiple_json_to_file(*args.multiple, count=args.count)
    elif args.backup:
        config_manager.backup_file(args.backup)
    elif args.range and args.count:
        range_str = args.range 
        start_file, end_file = range_str.split("-")
        config_manager.append_files_between_range(start_file, end_file, count=args.count)
    elif args.pepe:
        print_ascii_pepe()
    else:
        print("You did something wrong. Go help with python3 jft.py -h")
        

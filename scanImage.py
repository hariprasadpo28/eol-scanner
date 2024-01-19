import logging
import json
import subprocess
import re
import pandas as pd

class ImageScanner:
    def __init__(self, image):
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger("eol-images-scan")
        self.image_to_scan = image
            
    def get_os_name_general(self):
        """
        Get the os name by running general command in the docker container
        """
        self.logger.info("Going to process the image by running general command to find out os " + self.image_to_scan)
        
        general_command = subprocess.run(["docker","run","--entrypoint","cat","--memory-swap", "-1","--rm",self.image_to_scan,"/etc/os-release"], capture_output=True)
        result_data = []
        if general_command.returncode == 0:
            result = general_command.stdout
            if result:
                data = result.splitlines()
                processed_data = [process.decode().strip() for process in data]
                result_data = [line for line in processed_data if "NAME" in line or "PRETTY_NAME" in line or "VERSION" in line]
                return result_data
            
    def cleanup_image(self):
        """
        Delete the image after processing
        """
        try:
            delete_command = subprocess.run(["docker","rmi", self.image_to_scan], capture_output=True)
        except Exception as e:
            self.logger.info("Exception while deleting the image " + str(e))
    
    def run_syft(self):
        """
        Run syft on the image to get the os name
        """
        syft_op = subprocess.run(["syft","--scope","all-layers",self.image_to_scan,"-o","json"],capture_output=True)
        os_name = None
        if(syft_op.stdout and syft_op.returncode==0):
            distro=json.loads(syft_op.stdout)
            try:
                os_name=distro["distro"]["prettyName"]
            except Exception as e:
                os_name = distro["distro"]
        else:
            error_msg = syft_op.stderr.decode()
            if "could not fetch image" in error_msg:
                os_name = "No image available (Unable to pull)"
        return os_name
    
    def format_os_name_distroless(self, formatted_name):
        """
        Format the os name for distroless image
        """
        os_name = None
        try:
            name = re.search(r"VERSION=([\w\s\/\.\-\(\)\+\=\,\*\`\~\;\:\'\"\[\]\|\&\#]*)", formatted_name)
            if name is not None and name.group() is not None:
                os_name = name.groups(0)[0]
            if os_name is None:
                return self.format_os_name_actual(formatted_name)
            return os_name
        except Exception as e:
            self.logger.info("Exception while getting os name for distroless image " + str(e))
            

    def format_os_name_actual(self, formatted_name):
        """
        Format the os name for image (not on distroless)
        """
        try:
            name = re.search(r"NAME=([\w\s\/\.\-\(\)\+\=\,\*\`\~\;\:\'\"\[\]\|\&\#]*)", formatted_name)
            if name is not None and name.group() is not None:
                os_name = name.groups(0)[0]
                return os_name
        except Exception as e:
            self.logger.info("Exception while getting os name for distroless image " + str(e))    
    
    def format_os_name(self, result_os):
        """
        Format OS name from the result of general command
        """
        os_name = None
        try:
            formatted_name = "$".join(result_os).replace('"','')
            pretty_name = re.search(r"PRETTY_NAME=([\w\s\/\.\-\(\)\+\=\,\*\`\~\;\:\'\"\[\]\|\&\#]*)", formatted_name)
            if pretty_name is not None and pretty_name.group() is not None:
                os_name = pretty_name.groups(0)[0]
                if os_name == "Distroless":
                    distroless_os_name = self.format_os_name_distroless(formatted_name)
                    os_name = distroless_os_name if distroless_os_name else os_name
               
            else:
                os_name = self.format_os_name_actual(formatted_name)
            return os_name
        except Exception as e:
            self.logger.info("Exception while formatting os name for the image "+ self.image_to_scan + str(e))

            
    def get_os_name(self):
        """
        Get OS name by running general command and syft
        """
        os = {}
        os_name = None
        try:
            # Run the general command to get os name
            general_command_out = self.get_os_name_general()
            if general_command_out is not None and len(general_command_out) > 0:
                os_name = self.format_os_name(general_command_out)
            # If general command is not produces any result, try running syft    
            if os_name is None:
                syft_command = self.run_syft()
                if type(syft_command) is dict:
                    os['syft_results'] = syft_command
                    os['name'] = "NA"
                else:
                    os['name'] = syft_command  
            else:
                os['name'] = os_name                  
        except Exception as e:
            os['name'] = "NA - Tool(Syft and linux cmd) failed to find os"   
        return os
                
    def get_languages_by_os(self, os_name):
        """
        Get installed programming languages from package managers
        """
        # https://distrowatch.com/dwres.php?resource=package-management\
        pkg_manager_command = {
            "centos" : "rpm -q -a", "fedora": "rpm -q -a", "red": "rpm -q -a",
            "photon" : "yum list installed",
            "oracle linux" : "rpm -q -a",
            "alpine": "apk list -I",
            "debian": "apt list --installed", "ubuntu": "apt list --installed", 
            }  
        result_data = []       
        try:
            if os_name is not None:    
                osname = os_name.lower()
                for item in pkg_manager_command:
                    if item in osname:
                        command_to_execute = pkg_manager_command[item]
                        command_to_execute = command_to_execute.split()
                        languages_os = subprocess.run(["docker","run","--entrypoint",command_to_execute[0],"--memory-swap", "-1","--rm",self.image_to_scan,command_to_execute[1],command_to_execute[2]], capture_output=True)
                        
                        if languages_os.returncode == 0:
                            result = languages_os.stdout
                            if result:
                                data = result.splitlines()
                                processed_data = [process.decode().strip() for process in data]
                                result_data = [line for line in processed_data if \
                                    line.startswith("python") or line.startswith("go") or line.startswith("node") or \
                                    line.startswith("php") or line.startswith("libruby") or line.startswith("openjdk") or \
                                    line.startswith("angular") or line.startswith("react")]
                                return result_data
                        break
            return result_data
        except Exception as e:
            return result_data
    
    def run_individual_docker_run(self, languages):
        self.logger.info("Going to run individual language command for the image :"+ self.image_to_scan)
        language_command = {
            "python3" : "--version",
            "python2.7": "--version",
            "python2": "--version",
            "python": "--version",
            "go": "version",
            "php8": "--version",
            "php7": "--version",
            "php": "--version",
            "node" : "--version",
            "nodejs" : "--version",
            "ruby" : "--version",
            "java" : "-version",
            "angular": "version",
            "react": "-v"
        }
        resultant_data = {}
        for iterate_lang in languages:
            try:
                language = iterate_lang
                command = language_command[language]
                if language == "angular":
                    languages_os = subprocess.run(["docker","run","--entrypoint", "ng", "--memory-swap", "-1","--rm",self.image_to_scan,command],capture_output=True)
                elif language == "react":
                    languages_os = subprocess.run(["docker","run","--entrypoint", "npm", "--memory-swap", "-1","--rm",self.image_to_scan,"view", "react", "version"],capture_output=True)
                else:
                    languages_os = subprocess.run(["docker","run","--entrypoint", language, "--memory-swap", "-1","--rm",self.image_to_scan,command],capture_output=True)
                    
                if languages_os.returncode == 0:
                    result = languages_os.stdout
                    if result:
                        data = result.splitlines()
                        processed_data = [process.decode().strip() for process in data]
                        if language == "angular":
                            for i in processed_data:
                                if "Angluar CLI" in i:
                                    resultant_data[language] = i
                            continue
                        if len(processed_data) > 0 and processed_data[0] != '':
                            resultant_data[language] = processed_data[0]
                    else:
                        # Sometimes Error message holds the data
                        result_err = languages_os.stderr
                        if result_err:
                            data_err = result_err.splitlines()
                            processed_data_err = [process_err.decode().strip() for process_err in data_err]
                            if len(processed_data_err) > 0:
                                data_to_write = processed_data_err[0]
                                if "docker" not in data_to_write:
                                    resultant_data[language] = data_to_write
            except Exception as e:
                self.logger.info("Exception while running individual command "+ str(e))
        
        return resultant_data


    def run_individual_language_command(self):
        self.logger.info("Going to run bash script for individual commands for the image : "+ self.image_to_scan)
        language_command = [
            "python3",
            "python2.7",
            "python2",
            "python",
            "go",
            "php8",
            "php7",
            "php",
            "node",
            "nodejs",
            "ruby",
            'java',
            "angular",
            "react"
        ]
        resultant_data = {}
        try:
            path = subprocess.run(["pwd"], capture_output=True)
            path = path.stdout.decode('utf-8').strip()
            path = path+":/eol-mount/"
            process = subprocess.run(["docker", "run", "-v", path, "--rm", "--entrypoint", "sh", self.image_to_scan, "/eol-mount/utils/run_individual_commands.sh"], capture_output=True)
            if process.returncode == 0:
                #While running individual language command the error message also comes in stdout if it is not found, it will give error only if bash script is not found in the docker container.
                #So if bash is not present in the container, we'll run docker container for each language command
                if process.stderr.decode('utf-8').strip() != '':        
                    self.logger.info(f"Exception while running sh in the image: {self.image_to_scan}")
                    self.logger.info("Going to run individual docker commands for all languages")
                    resultant_data = self.run_individual_docker_run(self.image_to_scan, language_command)
                    return resultant_data
                versions = process.stdout.decode('utf-8').strip().split('#Separator#')
                for i in range(len(language_command)):
                    if "not found" in versions[i] or "/eol-mount/" in versions[i]:
                        continue
                    else:
                        # multiple versions os same language in a image are concatenated with ',' as a separator, this is used later to extract the numeric version of each found versions. 
                        # So here we remove the commas if present just to make sure there will be no invalid versions wile parsing.
                        if language_command[i] == 'react':
                            v = re.findall(
                                "[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", versions[i])
                            if v == []:
                                continue
                            else:
                                resultant_data[language_command[i]] = v[0]
                                continue
                        if language_command[i] == 'node' or language_command[i] == 'nodejs':
                            v = re.findall("[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", versions[i])
                            if v == []:
                                continue
                            else:
                                resultant_data[language_command[i]] = 'v'+v[0]
                                continue                            
                        if language_command[i] == "angular":
                            v = re.findall(
                                "[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", versions[i])
                            if v == []:
                                continue
                            else:
                                resultant_data[language_command[i]] = v[0]
                                continue
                        if language_command[i] == "java":
                            result = self.run_individual_docker_run(self.image_to_scan, ['java'])
                            if 'java' in result:
                                resultant_data[language_command[i]] = result['java']
                            continue
                        resultant_data[language_command[i]] = versions[i].replace(',', ' ')
        except Exception as e:
            self.logger.info("Exception while running bash script command "+ str(e))
        return resultant_data

    def check_if_library(self, path):
        """
        checking if the jar file is coming from the library (dependency)
        """
        if ("lib/" in path) or ("libs/" in path) or ("share/" in path):
            # Returning True if the jar/war is coming from library
            return True
        return False
    
    def parse_syft_output_java(self, output):
        try:
            artifacts = output["artifacts"] if "artifacts" in output else [] 
            if artifacts != []:
                versions = []
                paths = []
                for item in artifacts:
                    if 'metadata' in item:
                        if 'java' in item['foundBy']:
                            metadata = item["metadata"]
                            path = metadata['virtualPath'] if "virtualPath" in metadata else ""
                            if "manifest" in metadata:
                                if "main" in metadata["manifest"]:
                                    if "Build-Jdk" in metadata["manifest"]["main"]:
                                        java_version = metadata["manifest"]["main"]["Build-Jdk"]
                                        if path and not self.check_if_library(path):
                                           versions.append(java_version)
                                           paths.append(path + "("+ java_version + ")")
                return list(set(versions)), paths
        except Exception as e:
            self.logger.info("Exception while finding java version by syft: " + str(e))
            return None, None
        return None, None

    def parse_syft_output_react(self, output):
        try:
            artifacts = output['artifacts'] if "artifacts" in output else [] 
            if artifacts != []:
                versions = []
                paths = []
                for i in artifacts:
                    if i["name"] == "react":
                        if "version" in i:
                            version = i["version"]
                            versions.append(version)
                            if "locations" in i:
                                locations = i["locations"]
                                for item_loc in locations:
                                    if "path" in item_loc:
                                        path = item_loc["path"] +"("+version+")"
                                        paths.append(path)
                return list(set(versions)), paths

        except Exception as e:
            self.logger.info("Exception while finding react version by syft")
            return None, None
        return None, None

    def parse_syft_output_angular(self, output):
        try:
            artifacts = output['artifacts'] if "artifacts" in output else [] 
            if artifacts != []:
                versions = []
                paths = []
                for i in artifacts:
                    if i["name"] == "@angular-devkit/core" or i["name"] == "@angular/cli" or i["name"] == "@schematics/angular":
                        if "version" in i:
                            version = i["version"]
                            versions.append(version)
                            if "locations" in i:
                                locations = i["locations"]
                                for item_loc in locations:
                                    if "path" in item_loc:
                                        path = item_loc["path"] +"("+version+")"
                                        paths.append(path)
                return list(set(versions)), paths

        except Exception as e:
            self.logger.info("Exception while finding angular version by syft")
            return None, None
        return None, None

    def run_syft_to_get_binaries(self, syft_path):
        self.logger.info("running syft to get executable details")
        syft_op = subprocess.run(["syft","--config", syft_path, self.image_to_scan,"-o","json"],capture_output=True)
        
        if(syft_op.stdout and syft_op.returncode==0):
            syft_result=json.loads(syft_op.stdout)
            java_versions, java_paths = self.parse_syft_output_java(syft_result)
            angular_versions, angular_paths = self.parse_syft_output_angular(syft_result)         
            react_versions, react_paths = self.parse_syft_output_react(syft_result)    
            try:
                artifacts = syft_result["artifacts"] if "artifacts" in syft_result else []
                if artifacts != []:
                    versions = []
                    paths = []
                    # Found something related to go
                    for item in artifacts:
                        if "metadata" in item:
                            metadata = item["metadata"]
                            if "goCompiledVersion" in metadata:
                                go_version = metadata["goCompiledVersion"]
                                versions.append(go_version)
                                if "locations" in item:
                                    locations = item["locations"]
                                    for item_loc in locations:
                                        if "path" in item_loc:
                                            path = item_loc["path"] +"("+go_version+")"
                                            paths.append(path)
                    return list(set(versions)), paths, java_versions, java_paths, angular_versions, angular_paths, react_versions, react_paths
                            
            except Exception as e:
                self.logger.info("Exception while finding go version by syft: " + str(e))
                return None, None, java_versions, java_paths, angular_versions, angular_paths, react_versions, react_paths
        return None, None, None, None, None, None, None, None
    
    def extract_language(self, data, os):
        """
        extract the required programming languages from the package manager's result
        """
        final_dict = {}
        try:
            test=re.compile("(^go-\d)|(^python2)|(^python3)|(^php7)|(^php8)|(^nodejs)|(^libruby)|(^openjdk)|(^react)")
            for item in data:
                if test.match(item):
                    group = test.match(item).group()
                    if group == "libruby":
                        group = "ruby"
                    if group == "openjdk":
                        group = "java"
                    if "alpine" in os.lower():
                        final_dict[group] = item.split(" ")[0]
                    
                    elif "debian" in os.lower() or "ubuntu" in os.lower():
                        final_dict[group] = item.split(" ")[1]
                    else:
                        # This will handle all centos, fedora 
                        final_dict[group] = item
            return final_dict
        except Exception as e:
            self.logger.info("Exception while extracting language : "+ str(e))
            return final_dict
                           
    def get_scan_image(self, syft_path="utils/syft.template.yml"):
        self.logger.info("Going to process the image "+ self.image_to_scan)
        try:
            
            result_os_images = {}
            
            scan_image_details = {}
            result_data_languages_os = []
            result_data_languages_specific = {}
            syft_executables_go = None
            syft_path_go = None
            syft_executables_java = None
            syft_path_java = None
            syft_executables_angular = None
            syft_path_angular = None 
            syft_executables_react = None
            syft_path_react = None 

            os_name = self.get_os_name()
            scan_image_details["os"] = os_name
            
            #get programming languages by os (pakage manager)
            name_of_os = os_name['name'] if "name" in os_name else None
            result_data_languages_os = self.get_languages_by_os(name_of_os)
            result_data_languages_specific = self.run_individual_language_command()
            
            #Comparing the package manager result and individual language command result and removing the duplicates
            if result_data_languages_specific != {} and result_data_languages_os is not None and len(result_data_languages_os) > 0:
                matched_languages = list(result_data_languages_specific.keys())
                
                remove_languages = []
                for match in matched_languages:
                    for os_languages in result_data_languages_os:
                        if os_languages.startswith(match):
                            remove_languages.append(os_languages)
                
                result_data_languages_os = [item for item in result_data_languages_os if item not in remove_languages]
                scan_image_details["languages"] = result_data_languages_os
            else:
                scan_image_details["languages"] = result_data_languages_os
            
            
            #get programming languages - specific
            scan_image_details["languages-specific"] = result_data_languages_specific
       
            syft_executables_go, syft_path_go, syft_executables_java, syft_path_java, syft_executables_angular, syft_path_angular, syft_executables_react, syft_path_react = self.run_syft_to_get_binaries(syft_path)
            scan_image_details["languages-syft"] = [syft_executables_go, syft_executables_java, syft_executables_angular, syft_executables_react]

            scan_image_details["languages-syft-go-paths"] = syft_path_go
            scan_image_details["languages-syft-java-paths"] = syft_path_java
            scan_image_details["languages-syft-angular-paths"] = syft_path_angular
            scan_image_details["languages-syft-react-paths"] = syft_path_react
            
            self.logger.info("OS level programming languages ")
            self.logger.info(scan_image_details["languages"])
            
            self.logger.info("Default programming languages ")
            self.logger.info(scan_image_details["languages-specific"])
            result_os_images[self.image_to_scan] = {'scan_details': scan_image_details}
            
        except Exception as e:
            self.logger.info("Exception while getting scan image data " + str(e))
            
            prepare_data = {}
            prepare_data["languages"] = result_data_languages_os
            prepare_data["languages-specific"] = result_data_languages_specific
            prepare_data["languages-syft"] = [syft_executables_go, syft_executables_java, syft_executables_angular, syft_executables_react]
            prepare_data["languages-syft-go-paths"] = syft_path_go
            prepare_data["languages-syft-java-paths"] = syft_path_java
            prepare_data["languages-syft-angular-paths"] = syft_path_angular
            prepare_data["languages-syft-react-paths"] = syft_path_react
            
            result_os_images[self.image_to_scan] = {"scan_details": prepare_data}
            
        self.cleanup_image()
        return result_os_images

            
    def language_format_for_csv(self, languages):
        data = ''
        try:
            keys = languages.keys()
            for item in keys:
                formatted = item + ": "+languages[item]
                data = data + formatted + ","
            else:
                if len(data) > 0:
                    data = data[0:len(data) - 1]  
            return data 
        except Exception as e:
            self.logger.info("Exception while formatting data for csv: "+ str(e))  
            return data
    
    def binary_version_detect(self, language, version):
        version = version.split()
        binary_version_detect = {
                                 "python" : version[1] if len(version) > 2 else "".join(version),
                                 "python2" : version[1] if len(version) > 2 else "".join(version),
                                 "python2.7" : version[1] if len(version) > 2 else "".join(version),
                                 "python3" : version[1] if len(version) > 2 else "".join(version),
                                 "go": version[2] if len(version) > 3 else "".join(version),
                                 "php": version[1] if len(version) > 2 else "".join(version),
                                 "php7": version[1] if len(version) > 2 else "".join(version),
                                 "php8": version[1] if len(version) > 2 else "".join(version),
                                 "nodejs": version[0] if len(version) > 1 else "".join(version), 
                                 "node": version[0] if len(version) > 1 else "".join(version),
                                 "ruby": version[1] if len(version) > 1 else "".join(version),
                                 "java": version[2] if len(version) > 2 else "".join(version),
                                 "angular": version[2] if len(version) > 2 else "".join(version),
                                 "react": version[0]
                                 }
        return binary_version_detect[language]
    
    def seperate_by_language(self, oslanguages, languages_specific, languages_executables_go, languages_executables_java, languages_executables_angular, languages_executables_react):
        try:
            # Processing all the three columns "LanguagesByOS, LanguagesByGeneral, LanguagesByExecuatbles"
            go, python, php, node, ruby, java, angular, react   = [], [], [], [], [], [], [], []
            detect = {"go": go, "python": python, "php": php, "node": node, "ruby":ruby, "java": java, "angular": angular, "react": react}
            
            try:
                if oslanguages is not None and len(oslanguages) > 0:
                    for split_item in oslanguages:
                        if split_item is not None:
                            splitted_details = split_item.split(",")
                            for item in splitted_details:
                                if item is not None and item != '':
                                    split_version = item.split(": ")
                                    language = split_version[0]
                                    version = split_version[1]
                                    for pick in detect.keys():
                                        if pick in language:
                                            if len(detect[pick]) == 0:
                                                detect[pick].append("version: "+ version + "(os)")
                                            else:
                                                changed = detect[pick]
                                                changed[0] = changed[0] + "," + "version: "+ version + "(os)"
            except Exception as e:
                self.logger.info("Exception while processing os-level languages: " + str(e))
                                
            # Seperate it for languages specific 
            try:
                if languages_specific is not None and len(languages_specific) > 0:
                    for split_item in languages_specific:
                        if split_item is not None:
                            splitted_details = split_item.split(",")
                            for item in splitted_details:
                                if item is not None and item != '':
                                    split_version = item.split(": ")
                                    
                                    language = split_version[0]
                                    version = split_version[1]
                                    detected_binary_version = self.binary_version_detect(language, version)
                                    for pick in detect.keys():
                                        if pick in language:
                                            if len(detect[pick]) == 0:
                                                detect[pick].append("version: "+ detected_binary_version + "(default)")
                                            else:
                                                changed = detect[pick]
                                                changed[0] = changed[0] + "," + "version: "+ detected_binary_version + "(default)"
            except Exception as e:
                self.logger.info("Exception while processing language-specific results: " + str(e))
            
            #Parsing executables (golang version)
            try:
                if languages_executables_go is not None and len(languages_executables_go) > 0:
                    # and languages_executables[0] != '' and languages_executables[0] is not None:
                    # Currently only possible entry is go. so handling that alone
                    # go_executables = languages_executables[0]
                    # if go_executables is not None and len(go_executables) > 0:
                    for split_item in languages_executables_go:
                        if split_item is not None:
                            splitted_details = split_item.split(",")
                            for item in splitted_details:
                                if item is not None and item != '':
                                    if len(detect["go"]) == 0:
                                        detect["go"].append("version: "+ item + "(executable)")
                                    else:
                                        changed = detect["go"]
                                        changed[0] = changed[0] + "," + "version: "+ item + "(executable)"
            except Exception as e:
                self.logger.info("Exception while processing go-executables results: " +str(e))
            
            #Parsing executables (java version)
            try:
                if languages_executables_java is not None and len(languages_executables_java) > 0:
                    for split_item in languages_executables_java:
                        if split_item is not None:
                            splitted_details = split_item.split(",")
                            for item in splitted_details:
                                if item is not None and item != '':
                                    if len(detect["java"]) == 0:
                                        detect["java"].append("version: "+ item + "(executable)")
                                    else:
                                        changed = detect["java"]
                                        changed[0] = changed[0] + "," + "version: "+ item + "(executable)"
            except Exception as e:
                self.logger.info("Exception while processing java-executables results: "+str(e))

            #Parsing executables (react version)
            try:
                if languages_executables_react is not None and len(languages_executables_react) > 0:
                    for split_item in languages_executables_react:
                        if split_item is not None:
                            splitted_details = split_item.split(",")
                            for item in splitted_details:
                                if item is not None and item != '':
                                    if len(detect["react"]) == 0:
                                        detect["react"].append("version: "+ item + "(executable)")
                                    else:
                                        changed = detect["react"]
                                        changed[0] = changed[0] + "," + "version: "+ item + "(executable)"   
            except Exception as e:
                self.logger.info("Exception while processing react-executables results: "+str(e))

            #Parsing executables (angular version)
            try:
                if languages_executables_angular is not None and len(languages_executables_angular) > 0:
                    for split_item in languages_executables_angular:
                        if split_item is not None:
                            splitted_details = split_item.split(",")
                            for item in splitted_details:
                                if item is not None and item != '':
                                    if len(detect["angular"]) == 0:
                                        detect["angular"].append("version: "+ item + "(executable)")
                                    else:
                                        changed = detect["angular"]
                                        changed[0] = changed[0] + "," + "version: "+ item + "(executable)"        
            except Exception as e:
                self.logger.info("Exception while processing angular-executables results: "+str(e))                            
        except Exception as e:
            self.logger.info("Exception while seperating the languages " + str(e)) 
        
        go = ",".join(set(go[0].split(","))) if len(go) > 0 else " "
        python = ",".join(set(python[0].split(","))) if len(python) > 0 else " "
        php = ",".join(set(php[0].split(","))) if len(php) > 0 else " "
        node = ",".join(set(node[0].split(","))) if len(node) > 0 else " "
        ruby = ",".join(set(ruby[0].split(","))) if len(ruby) > 0 else " "
        java = ",".join(set(java[0].split(","))) if len(java) > 0 else " "
        angular = ",".join(set(angular[0].split(","))) if len(angular) > 0 else " "
        react = ",".join(set(react[0].split(","))) if len(react) > 0 else " "
        return go, python, php, node, ruby, java, angular, react                    
                
    def create_csv_file(self, scan_image_data):
        image_names = []
        os = []
        os_languages = []
        languages_specific = []
        languages_executables_go = []
        languages_executables_java = []
        languages_executables_angular = []
        languages_executables_react = []
        go_list, python_list,php_list, node_list, ruby_list, java_list, angular_list, react_list = [], [], [], [], [], [], [], []
        try:
            
            image_names.append(self.image_to_scan)
            os.append(scan_image_data[self.image_to_scan]['scan_details']['os']['name'])
            
            oslanguages = scan_image_data[self.image_to_scan]['scan_details']['languages']
            if type(oslanguages) is list:
                extract_os_languages = self.extract_language(oslanguages, scan_image_data[self.image_to_scan]['scan_details']['os']['name'])
                os_format = self.language_format_for_csv(extract_os_languages)
                os_languages.append(os_format)
            else:
                os_languages.append(oslanguages)
                
            languagesspecific = scan_image_data[self.image_to_scan]['scan_details']['languages-specific']
            if type(languagesspecific) is dict:
                language_format = self.language_format_for_csv(languagesspecific)
                languages_specific.append(language_format)
            else:
                languages_specific.append(languagesspecific)
                            
            executablelanguages = scan_image_data[self.image_to_scan]['scan_details']['languages-syft']
            if type(executablelanguages[0]) is list:
                languages_executables_go.append(",".join(executablelanguages[0]))
            else:
                languages_executables_go.append(executablelanguages[0])

            if type(executablelanguages[1]) is list:
                languages_executables_java.append(",".join(executablelanguages[1]))
            else:
                languages_executables_java.append(executablelanguages[1])

            if type(executablelanguages[2]) is list:
                languages_executables_angular.append(",".join(executablelanguages[2]))
            else:
                languages_executables_angular.append(executablelanguages[2])

            if type(executablelanguages[3]) is list:
                languages_executables_react.append(",".join(executablelanguages[3]))
            else:
                languages_executables_react.append(executablelanguages[3])
            
            # Aggergate by programs irrespective of type(os, binary, execuatble)
            go, python, php, node, ruby, java, angular, react = self.seperate_by_language(os_languages, languages_specific, languages_executables_go, languages_executables_java, languages_executables_angular, languages_executables_react)
            
            # Data prepartion for CSV - programming languages
            go_list.append(go)
            python_list.append(python)
            php_list.append(php)
            node_list.append(node)
            ruby_list.append(ruby)
            java_list.append(java)
            angular_list.append(angular)
            react_list.append(react)
            
        except Exception as e:
            self.logger.info("Exception while converting into csv " + str(e))
        
        final_data = {
            'Image name' : image_names, 'Base OS' : os, 
            'Python' : python_list, 'Go' : go_list, 'Php' : php_list, 'Node' : node_list, "Ruby": ruby_list, "Java": java_list, "Angular": angular_list, "React": react_list
            }
        df = pd.DataFrame(final_data)
        return df
        
    def write_updated_json(self, filename, result_os_images):
        
        self.logger.info("Going to prepare the csv file")
        with open(filename+".json", "w") as f:
            json.dump(result_os_images, f)
        dataframe = self.create_csv_file(result_os_images)
        self.cleanup_image()
        return dataframe

    def cleanup_docker_space(self):
        try:
            delete_command = subprocess.run(["docker","system", "prune", "-a", "-f"], capture_output=True)
        except Exception as e:
            self.logger.info("Exception while deleting the docker space " + str(e))

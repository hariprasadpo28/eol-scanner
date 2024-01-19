from collections import defaultdict
import re
import requests
from datetime import datetime
from dateutil.parser import parse


class EOLArtifacts():
    def __init__(self, logger):
        self.logger = logger
        self.imagenames, self.baseoss, \
            self.python_langs, self.go_langs, self.php_langs, self.node_langs, self.ruby_langs, \
            self.java_langs, self.angular_langs, self.react_langs = [
            ], [], [], [], [], [], [], [], [], []
        self.eol_scan_results = {}
        self.apiData = {}
        self.today = datetime.today()


    # Function to get the eol data for all released versions of the below mentioned programming languages
    # Programming Languages - "go","python","node","ruby","react","php","kotlin","java","laravel","jquery","django","angular"
    def get_eol_data(self):
        self.logger.info("Getting EOL data from endoflife.date")
        apiData = defaultdict(dict)
        url = "https://endoflife.date/api/"
        products = ["go", "python", "node", "ruby", "react", "php",
                    "kotlin", "java", "laravel", "jquery", "django", "angular"]
        for i in products:
            re = requests.get(url + i + ".json")
            json_data = re.json()
            apiData[i] = defaultdict(dict)
            for j in json_data:
                apiData[i][j['cycle']] = {
                    'eol': j['eol'], 'latest': j['latest']}
        return apiData

    # Function to parse the version and getting the eol status of that version
    def parse_version(self, version, lang):
        try:
            latest_version = self.apiData[lang][list(
                self.apiData[lang].keys())[0]]['latest']
        except:
            latest_version = list(self.apiData[lang].keys())[0]
        affected_versions = []
        eol_ = False
        text = ""
        version = version.split(',')
        for i in version:
            i = i.split('version: ')[1]
            if lang == 'go':
                v = re.findall("[0-9]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0]
                temp = v.split('.')[-1]
                if int(temp) < 10:
                    affected_versions.append(i)
                    eol_ = True
                    continue
            if lang == 'python':
                v = re.findall("[2-3]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0]
            if lang == "node":
                v = re.findall("[0-9]*[0-9]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0]
                v = v.split(".")[0]
            if lang == "php":
                v = re.findall("[0-9]*[0-9]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0]
            if lang == "angular":
                v = re.findall(
                    "[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0].split(".")
                v = v[0]
                if int(v) < int('9'):
                    affected_versions.append(i)
                    eol_ = True
                    continue
            if lang == "react":
                v = re.findall(
                    "[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0].split(".")
                v = v[0]
                if int(v) < int('17'):
                    affected_versions.append(i)
                    eol_ = True
                    continue
            if lang == "ruby":
                v = re.findall(
                    "[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0]
                v = v.split(".")
                v = v[0]+"."+v[1]
            if lang == "java":
                v = re.findall(
                    "[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", i)
                if v == []:
                    continue
                v = v[0]
                v = v.split(".")
                if v[0] == "1":
                    v = v[1]
                    if int(v) < int('6'):
                        affected_versions.append(i)
                        eol_ = True
                        continue
                else:
                    v = v[0]
                

            if v in self.apiData[lang].keys():
                eol = self.apiData[lang][v]['eol']
                if eol != True and eol != False:
                    date = parse(eol)
                    eol = date < self.today
                eol_ = eol_ or eol
                if eol:
                    affected_versions.append(i)
            else:
                continue
        text = "Affected Versions: " + \
            "; ".join(affected_versions) + " \n" + \
            "Latest Version: " + str(latest_version)
        upgrade = "Yes" if eol_ == True else "No"
        return upgrade, text

    def reformat_java_version(self, version):
        if version == "" or version ==" ":
            return version
        versions = version.split(",")
        formatted_versions = []
        for i in versions:
            i = i.split('version: ')
            v = re.findall("[0-9]*[0-9]+[.]+[0-9]*[0-9]+[.]+[0-9]*[0-9]", i[1])
            if v == []:
                continue
            v = v[0].split(".")
            if v[0] == "1":
                version_ = "version: " + ".".join(v[1:]) + f"({i[1]})" 
            else:
                version_ = "version: " + i[1]
            formatted_versions.append(version_)
        return ",".join(formatted_versions)

    def add_eol_columns(self, data):
        self.logger.info("Verifying the version eol status and updating the data")
        languages = ["Python", "Go", "Php", "Node", "Ruby",
                     "Java", "Angular", "React"]
        eol_upgrade_details = {}
        upgrade_overall = []
        for i in languages:
            eol_details = []
            upgrade_req = []
            for j in range(len(data[i])):
                if i == "Java":
                    data[i][j] = self.reformat_java_version(data[i][j])
                if data[i][j] != " " and data[i][j] != "":
                    upgrade, eol = self.parse_version(data[i][j], i.lower())
                    if upgrade == "No":
                        eol = ""
                else:
                    upgrade, eol = "", ""
                eol_details.append(eol)
                upgrade_req.append(upgrade)
            eol_upgrade_details[i + " - Eol Details"] = eol_details
            eol_upgrade_details[i + " - Upgrade Required?"] = upgrade_req

        bool_dict = {"No": False, "Yes": True, "": False}

        for i in range(len(data["Python"])):
            temp = False
            for j in languages:
                temp = temp or bool_dict[eol_upgrade_details[j +
                                                             " - Upgrade Required?"][i]]
            upgrade_overall.append("Yes" if temp == True else "No")

        final_data = {
            'Image name': data['Image name'], 'Base OS': data['Base OS'],
            'Python': data['Python'], "Python - Upgrade Required?": eol_upgrade_details["Python - Upgrade Required?"], "Python - Eol Details": eol_upgrade_details["Python - Eol Details"],
            'Go': data['Go'], "Go - Upgrade Required?": eol_upgrade_details["Go - Upgrade Required?"], "Go - Eol Details": eol_upgrade_details["Go - Eol Details"],
            'Php': data['Php'], "Php - Upgrade Required?": eol_upgrade_details["Php - Upgrade Required?"], "Php - Eol Details": eol_upgrade_details["Php - Eol Details"],
            'Node': data["Node"], "Node - Upgrade Required?": eol_upgrade_details["Node - Upgrade Required?"], "Node - Eol Details": eol_upgrade_details["Node - Eol Details"],
            'Ruby': data["Ruby"], "Ruby - Upgrade Required?": eol_upgrade_details["Ruby - Upgrade Required?"], "Ruby - Eol Details": eol_upgrade_details["Ruby - Eol Details"],
            'Java': data["Java"], "Java - Upgrade Required?": eol_upgrade_details["Java - Upgrade Required?"], "Java - Eol Details": eol_upgrade_details["Java - Eol Details"],
            'Angular': data["Angular"], "Angular - Upgrade Required?": eol_upgrade_details["Angular - Upgrade Required?"], "Angular - Eol Details": eol_upgrade_details["Angular - Eol Details"],
            'React': data["React"], "React - Upgrade Required?": eol_upgrade_details["React - Upgrade Required?"], "React - Eol Details": eol_upgrade_details["React - Eol Details"],

            "Upgrade Required ?": upgrade_overall
        }
        return final_data

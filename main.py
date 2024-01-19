import sys
from scanImage import ImageScanner
from addEolStatus import EOLArtifacts
import logging
import pandas as pd

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("eol-images-scan")


if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        logging.info("Please provide image with tag to scan")
        exit(0)
        
    image_to_scan = sys.argv[1]
    result = {}
    image_scanner = ImageScanner(image_to_scan)
    result = image_scanner.get_scan_image(syft_path='utils/syft.template.yml')
    file_name = image_to_scan.replace(':','_')
    file_name = file_name.replace('/','_')
    scan_data = image_scanner.write_updated_json(file_name, result)
    
    #prepare final data with EOL status
    eol_artifacts = EOLArtifacts(logger)
    eol_artifacts.apiData = eol_artifacts.get_eol_data()
    final_data_with_eol = eol_artifacts.add_eol_columns(scan_data)
    
    #Create CSV file with final data
    df = pd.DataFrame(final_data_with_eol)
    df.to_csv("eol-scan-results.csv", index=False)
    logger.info(" Final CSV file is generated")
    

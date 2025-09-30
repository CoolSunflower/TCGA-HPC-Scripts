import pandas as pd
from pathlib import Path
from tqdm import tqdm

# Need to change this to the name of the root folder 
RootFolder = "multiomics"
FeatureCount = 100
# FeatureMethod = 2
EnvironmentName = "myenv"

script_format = '''#!/bin/bash
#SBATCH --job-name={job}
#SBATCH --output={RootFolder}/o_e_files/{job}.o%j
#SBATCH --error={RootFolder}/o_e_files/{job}.e%j
#SBATCH --time=1-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1                         # Number of tasks
#SBATCH --ntasks-per-node=8
#SBATCH -A isaac-uthsc0057
#SBATCH --cpus-per-task=8                  # CPUs per task
#SBATCH --mem=32G                           # Total memory
#SBATCH --partition=ai-tenn                   # Partition name
#SBATCH --qos=ai-tenn               # AI-TENN QoS
#SBATCH --gres=gpu:1 

# Load any necessary modules
module load anaconda3/2024.06
source $ANACONDA3_SH
conda activate {ENVIRONMENT_NAME}

echo "The environment has been activated."

python -u {RootFolder}/main.py --data_Category Race --omicsConfiguration combination --DDP_group {DDP_GROUP} --cancer_type {CANCER_TYPE} --endpoint {ENDPOINT} --years {TIME} --features_count {FEATURE_COUNT} --FeatureMethod {FEATURE_METHOD} --omics_feature {FEATURE_STRING}

echo "The execution has been done."
'''

def clean_feature_string(feature_str):
    cleaned = str(feature_str).replace("(", "").replace(")", "").replace("'", "").replace('"', '')
    features = [f.strip() for f in cleaned.split(',')]
    return '_'.join(features)

def generate_task_name(data_category, cancer_type, ddp_group, omics_feature, endpoint, years, feature_method_name, features_count):
    return f'TCGA-{data_category}-{cancer_type}-{ddp_group}-{omics_feature}-{endpoint}-{years}YR_{feature_method_name}-{features_count}Features'

def process_two_feature_file(file_path, scripts_dir, sbatch_commands):
    print(f"Processing two-feature file: {file_path}")
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    
    for _, row in tqdm(df.iterrows()):
        cancer_type = row['Cancer Type']
        feature_type = row['Feature Type']
        endpoint = row['Clinical Outcome Endpoint']
        years = row['Event Time Threshold (Year)']
        target_group = row['Target Group']
        
        feature_string = clean_feature_string(feature_type)
        
        data_category = 'Race'
        ddp_group = target_group

        for FeatureMethod in [0,1,2,3]:
            feature_method_name = f'Method{FeatureMethod}'
            
            task_name = generate_task_name(
                data_category, cancer_type, ddp_group, feature_string, 
                endpoint, years, feature_method_name, FeatureCount
            )
            
            script_content = script_format.format(
                job=task_name,
                RootFolder=RootFolder,
                DDP_GROUP=ddp_group,
                CANCER_TYPE=cancer_type,
                ENDPOINT=endpoint,
                TIME=years,
                FEATURE_COUNT=FeatureCount,
                FEATURE_METHOD=FeatureMethod,
                FEATURE_STRING=feature_string,
                ENVIRONMENT_NAME=EnvironmentName
            )
            
            script_file = scripts_dir / f"{task_name}.sh"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Add sbatch command
            sbatch_commands.append(f"sbatch {RootFolder}/{task_name}.sh")
        
def process_multi_feature_file(file_path, scripts_dir, sbatch_commands):
    print(f"Processing multi-feature file: {file_path}")

    excel_file = pd.ExcelFile(file_path)
    worksheets = ['BLACK', 'ASIAN', 'NAT_A']
    
    for sheet_name in worksheets:
        if not sheet_name in excel_file.sheet_names:
            print(f"Warning: Sheetname {sheet_name} not found")
            continue

        print(f"Processing worksheet: {sheet_name}")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        for _, row in tqdm(df.iterrows(), desc=f"{sheet_name}"):
            cancer_type = row['Cancer_type']
            feature_type = row['Feature_type']
            endpoint = row['Target']
            years = row['Years']
            
            feature_string = clean_feature_string(feature_type)
            
            data_category = 'Race'
            ddp_group = sheet_name

            for FeatureMethod in [0,1,2,3]:
                feature_method_name = f'Method{FeatureMethod}'
                
                task_name = generate_task_name(
                    data_category, cancer_type, ddp_group, feature_string, 
                    endpoint, years, feature_method_name, FeatureCount
                )
                
                script_content = script_format.format(
                    job=task_name,
                    RootFolder=RootFolder,
                    DDP_GROUP=ddp_group,
                    CANCER_TYPE=cancer_type,
                    ENDPOINT=endpoint,
                    TIME=years,
                    FEATURE_COUNT=FeatureCount,
                    FEATURE_METHOD=FeatureMethod,
                    FEATURE_STRING=feature_string,
                    ENVIRONMENT_NAME=EnvironmentName
                )
                
                script_file = scripts_dir / f"{task_name}.sh"
                with open(script_file, 'w') as f:
                    f.write(script_content)
                
                sbatch_commands.append(f"sbatch {RootFolder}/{task_name}.sh")

def main():
    tasks_dir = Path("tasks")

    scripts_dir = tasks_dir / "scripts"    
    scripts_dir.mkdir(exist_ok=True)
    
    sbatch_commands = []
    
    two_feature_file = tasks_dir / "MLTasks_TwoFeaturesCombinations_Year02.xlsx"
    if two_feature_file.exists():
        process_two_feature_file(two_feature_file, scripts_dir, sbatch_commands)
    else:
        print(f"Warning: {two_feature_file} not found")
    
    three_feature_file = tasks_dir / "MLTasks_ThreeFeaturesCombinations_Year03.xlsx"
    if three_feature_file.exists():
        process_multi_feature_file(three_feature_file, scripts_dir, sbatch_commands)
    else:
        print(f"Warning: {three_feature_file} not found")
    
    four_feature_file = tasks_dir / "MLTasks_FourFeaturesCombinations_Year04.xlsx"
    if four_feature_file.exists():
        process_multi_feature_file(four_feature_file, scripts_dir, sbatch_commands)
    else:
        print(f"Warning: {four_feature_file} not found")
    
    with open("script.txt", 'w') as f:
        for command in sbatch_commands:
            f.write(command + '\n')
    
    print(f"\nGenerated {len(sbatch_commands)} scripts and saved sbatch commands to script.txt")
    print(f"All script files saved in: {scripts_dir}")

if __name__ == "__main__":
    main()


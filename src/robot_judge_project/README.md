# Course Project: Building a Robot Judge, Spring 2019
## Project Report
The Project report was made with LaTeX. Its source can be found in the [report](https://gitlab.ethz.ch/pascscha/robot_judge_project/blob/master/report) folder. The file [report/report.pdf](https://gitlab.ethz.ch/pascscha/robot_judge_project/blob/master/report/report.pdf) contains the actual pdf version of the report.

## Code
### Data Aquisition
The data needed for the machine learning part is contained in the file `code/data/data.json`. It consists of different ballots, their leaflet texts in different languages and the voting results by canton. In order to get this file you have to execute the [code/download_data.py](https://gitlab.ethz.ch/pascscha/robot_judge_project/blob/master/code/download_data.py) file:
```
cd code
python3 download_data.py
```

### Main Program
The main program is located in the file [code/main.py](https://gitlab.ethz.ch/pascscha/robot_judge_project/blob/master/code/main.py) if you run this program:
```
cd code
python3 main.py
```
When running this program, it will show you a list of avialable functions:
```
Availabe functions:
0: Neural Net N Grams
1: Sentiment Plots
2: Metadata Plots
Which function would you like to run?
```
Simply enter the index of the function you would like to run.

1. **Neural Net N Grams**

    This will train Neural networks on N Grams extracted from the data. The results will be stored in the [code/outfile.json](https://gitlab.ethz.ch/pascscha/robot_judge_project/blob/master/code/outfile.json) file.

2. **Sentiment Plots**

    This will run sentiment analysis on the data and visualize it into the [code/plots/sentiments](https://gitlab.ethz.ch/pascscha/robot_judge_project/blob/master/code/plots/sentiments) folder.

2. **Metadata Plots**

    This will run create plots of the metadata and store them in the [code/plots/metadata](https://gitlab.ethz.ch/pascscha/robot_judge_project/blob/master/code/plots/metadata)  folder.

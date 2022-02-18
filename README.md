# RankingMutants
 
This is the code and supplement for our IUI 22 paper "How Do People Rank Multiple Mutant Agents?"

This is NOT a living development repo, so pull requests will be ignored. We suggest cloning the repo if you want to edit the source.

## Installation Instructions for PyCharm
1. Clone this repository to your local machine.
2. Launch PyCharm
3. Create a new project (E.g. NewProject) in a virtual environment using Python 3.7
interpreter (change, if it’s not default settings)
4. Click on Add Configurations (Windows) or Edit Configurations (Mac)
5. Click +, choose “Python”, and name in "main"
6. Set the script path to “main.py” file (located in the "src" folder)
7. Set the working directory to the "src" folder and click OK
8. Go to Settings (File > Settings), and click on the directory you created the virtual
environment in (E.g. NewProject), and click on “Project Interpreter”
9. Click the +, and add the following packages: “PyOpenGL”, “wxPython”, and “torch” (by
typing the packages into the search bar)
10. Application is ready to run “main.py”

## Study Change Log
1. Participants 1-3 could not access the rewind feature, since it was not implemented yet
2. Colors changed after P3 and again after P7
3. Bug fixes involving: preventing a tab freeze that damaged part of P08’s data, improving
logging, and highlighting moves chosen in Scores on-the-Board explanation

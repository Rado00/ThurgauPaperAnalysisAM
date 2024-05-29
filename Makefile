run:
	@echo "Creating the requirements.txt file"
	pip freeze > requirements.txt
	@echo "Pushing the changes to the repository"
	git add .
	git commit -m "Update `date +'%Y/%m/%d %H:%M:%S'`"
	git push
	@echo "Pushed the changes to the repository successfully"

pull:
	@echo "Pulling the changes from the repository"
	git pull
	@echo "Pulled the changes from the repository successfully"

install:
	@echo "Installing the required packages"
	pip install -r requirements.txt
	@echo "Installed the required packages successfully"



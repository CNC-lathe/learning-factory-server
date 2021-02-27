# learning-factory-server
This repository houses the server code for the Learning Factory. Allows for connections between machines and the Digital Dashboard and Virtual Factory.

## Installation Instructions
First, ensure that you have the latest build tools installed on your machine:
```
python3 -m pip install --upgrade build
python3 -m build
```

Then, you can install the `learning-factory-server` package as follows:
```
python3 -m pip install -e .
```

## Testing Instructions
You can run the test suite with the following command:
```
tox
```

# backend-interview-project

A simple API that aquires some JSON data, processes the data and sends it to another API

1. the API sends a GET request to an external API
2. a JSON file containing duel data between 'enemy' and 'myself' is received
3. the raw damage is calculated
4. talents (stat modifications) are applied to both entities
5. the effective damage is calculated by applying armour mitigation
6. the effective damage is sent to another API for verification
7. the verifier API responds, indicating whether the effective damage is correct or not, together with the correct effective damage

the effective damage calculated by the verifier API is not always equal to the one sent by our API, because of rounding differences (the differences are less than 1 stat point) and because the verifier API allows attack values under 0 while our API sets the minimum value to 0 and, only for armour stats, the maximum value to 100 since it's a % mitigation.

## contents

- app.py : main app
- test.py : unit tests
- talents.json : all talents that can be applied
- example_data.json : data example from the assignment pdf
- tests_data/ : mock data for unit tests
- requirements.txt : dependencies
- assignment.pdf : instructions for the assignment

## how to run

1. Install dependencies with 'pip install -r requirements.txt'
2. Run 'app.py' on your local machine
3. Go to 'localhost:5000/run' to start the computation
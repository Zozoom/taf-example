*** Settings ***
Library    RequestsLibrary

*** Keywords ***
Check Service Is Alive
    Create Session    api    ${BASE_URL}    timeout=${TIMEOUT}
    ${response}=    GET On Session    api    /status/200
    Status Should Be    200    ${response}

Check Echo Endpoint
    Create Session    api    ${BASE_URL}    timeout=${TIMEOUT}
    ${response}=    POST On Session    api    /post    json={"ping": "pong"}
    Status Should Be    200    ${response}

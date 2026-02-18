*** Settings ***
Library    RequestsLibrary
Suite Setup    Create Session    api    ${BASE_URL}    timeout=${TIMEOUT}

*** Test Cases ***
Health Check Returns 200
    [Tags]    smoke
    ${response}=    GET On Session    api    /status/200
    Status Should Be    200    ${response}

Echo Body On POST
    [Tags]    smoke
    &{payload}=    Create Dictionary    ping=pong
    ${response}=    POST On Session    api    /post    json=${payload}
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    Should Be Equal    ${json["json"]["ping"]}    pong

Returns Sent Headers
    [Tags]    smoke
    &{headers}=    Create Dictionary    X-Correlation-Id=test-123
    ${response}=    GET On Session    api    /headers    headers=${headers}
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    Should Be Equal    ${json["headers"]["X-Correlation-Id"]}    test-123

Query Parameters Reflected
    [Tags]    smoke
    ${response}=    GET On Session    api    url=/get    params=feature=robot&env=test
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    Should Be Equal    ${json["args"]["feature"]}    robot
    Should Be Equal    ${json["args"]["env"]}    test

Delayed Response Still Succeeds
    [Tags]    smoke
    ${response}=    GET On Session    api    /delay/1
    Status Should Be    200    ${response}


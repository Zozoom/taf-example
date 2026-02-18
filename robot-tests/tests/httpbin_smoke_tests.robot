*** Settings ***
Library    RequestsLibrary
Library    Collections
Suite Setup    Create Session    api    ${BASE_URL}    timeout=${TIMEOUT}

*** Test Cases ***
Health Check Returns 200
    [Tags]    smoke    regression
    ${response}=    GET On Session    api    /status/200
    Status Should Be    200    ${response}

Echo Body On POST
    [Tags]    smoke    regression
    &{payload}=    Create Dictionary    ping=pong
    ${response}=    POST On Session    api    /post    json=${payload}
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    ${body}=    Get From Dictionary    ${json}    json
    ${echoed}=    Get From Dictionary    ${body}    ping
    Should Be Equal    ${echoed}    pong

Returns Sent Headers
    [Tags]    smoke    regression
    &{headers}=    Create Dictionary    X-Correlation-Id=test-123
    ${response}=    GET On Session    api    /headers    headers=${headers}
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    ${headers}=    Get From Dictionary    ${json}    headers
    ${sent}=    Get From Dictionary    ${headers}    X-Correlation-Id
    Should Be Equal    ${sent}    test-123

Query Parameters Reflected
    [Tags]    smoke    regression
    ${response}=    GET On Session    api    url=/get    params=feature=robot&env=test
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    ${args}=    Get From Dictionary    ${json}    args
    ${feature}=    Get From Dictionary    ${args}    feature
    ${env}=    Get From Dictionary    ${args}    env
    Should Be Equal    ${feature}    robot
    Should Be Equal    ${env}    test

Delayed Response Still Succeeds
    [Tags]    smoke    regression
    ${response}=    GET On Session    api    /delay/0
    Status Should Be    200    ${response}

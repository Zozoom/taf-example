*** Settings ***
Library    RequestsLibrary
Suite Setup    Create Session    api    ${BASE_URL}    timeout=${TIMEOUT}

*** Test Cases ***
Get Invalid Path Returns 404
    [Tags]    fail
    ${response}=    GET On Session    api    /invalid-path-xyz    expected_status=any
    Status Should Be    200    ${response}

Post To Nonexistent Endpoint
    [Tags]    fail
    &{payload}=    Create Dictionary    key=value
    ${response}=    POST On Session    api    /nonexistent/post    json=${payload}    expected_status=any
    Status Should Be    200    ${response}

Delete Invalid Resource
    [Tags]    fail
    ${response}=    DELETE On Session    api    /wrong/delete    expected_status=any
    Status Should Be    200    ${response}

Patch Nonexistent Path
    [Tags]    fail
    &{payload}=    Create Dictionary    data=test
    ${response}=    PATCH On Session    api    /bad-patch-endpoint    json=${payload}    expected_status=any
    Status Should Be    200    ${response}

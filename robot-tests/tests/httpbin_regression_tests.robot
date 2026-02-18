*** Settings ***
Library    RequestsLibrary
Library    Collections
Suite Setup    Create Session    api    ${BASE_URL}    timeout=${TIMEOUT}

*** Test Cases ***
Returns Random Bytes
    [Tags]    regression
    ${response}=    GET On Session    api    /bytes/32
    Status Should Be    200    ${response}
    ${length}=    Get Length    ${response.content}
    Should Be Equal As Integers    ${length}    32

Returns UUID
    [Tags]    regression
    ${response}=    GET On Session    api    /uuid
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    Dictionary Should Contain Key    ${json}    uuid
    ${uuid}=    Get From Dictionary    ${json}    uuid
    Should Match Regexp    ${uuid}    ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$

Get Cookies Returns Object
    [Tags]    regression
    ${response}=    GET On Session    api    /cookies
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    Dictionary Should Contain Key    ${json}    cookies

Delete Request Succeeds
    [Tags]    regression
    ${response}=    DELETE On Session    api    /delete    json={"deleted": true}
    Status Should Be    200    ${response}

Patch Request Succeeds
    [Tags]    regression
    &{payload}=    Create Dictionary    patched=yes
    ${response}=    PATCH On Session    api    /patch    json=${payload}
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    ${body}=    Get From Dictionary    ${json}    json
    ${val}=    Get From Dictionary    ${body}    patched
    Should Be Equal    ${val}    yes

Gzip Response Decompresses
    [Tags]    regression
    ${response}=    GET On Session    api    /gzip
    Status Should Be    200    ${response}
    ${json}=    Evaluate    $response.json()    modules=requests
    Dictionary Should Contain Key    ${json}    gzipped
    ${gzipped}=    Get From Dictionary    ${json}    gzipped
    Should Be True    ${gzipped}

Html Endpoint Returns Content
    [Tags]    regression
    ${response}=    GET On Session    api    /html
    Status Should Be    200    ${response}
    Should Contain    ${response.text}    <
    ${length}=    Get Length    ${response.text}
    Should Be True    $length > 100

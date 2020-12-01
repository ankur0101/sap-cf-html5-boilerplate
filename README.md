# SAP Cloud Foundry - HTML5 Boilerplate
Python Flask based server to run HTML5 apps, Destinations and Cloud Connector in SAP Cloud Foundry (just as SAP Cloud Platform Neo Trial) without code change. A destination with identical name from Neo Trial would be required. At the moment, app level Authentication mechanism is not supported.

### Usage
 - Clone this repository and place your applications inside `/webapp` directory.
 - Install Cloud Foundry client and login to API using command 
     ```sh
    cf login -a <URL>
    ```
 - Set your Cloud Foundry app name in manifest.yml.
    ```yml 
    name: <My-Sweet-App>
    ```
 - Deploy using command.
    ```sh
    cf push
    ```
### Prerequisite
Following services from SAP Cloud Foundry marketplace must get binded to your app as below

| Name | Service | Plan |
| ------ | ------ | ------ |
| connectivity_service | connectivity | lite |
| destination_service | destination | lite |
| uaa_service | xsuaa | application |

Their names are require to set in User Provided Variables as below:

| Key | Value |
| ------ | ------ |
| CONNECTIVITY_SRV | connectivity_service |
| DESTINATION_SRV | destination_service |
| UAA_SRV | uaa_service |
| DESTINATIONS | dest1,dest2 |

Cheers!

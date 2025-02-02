# VCC Mining?

This repository contains a variety of tools for:
 1. Collecting mapping data from VCCs to their fixing commits 
 2. Calculating vulnerability age metrics on such mappings
 
## Table of Contents
 - [Prerequisites](#prerequisites)
 - [VCCMapper](#mapping-cves-to-fixing-commits)
 - [Lifetime Estimation](#lifetime-estimation)
 - [Authors](#authors)
 
## Prerequisites
The tools in this repository require some conditions to be met in order to work correctly.
### Database
Mapping data between CVEs and fixing commits is stored and pulled from a mysql database. 
Please setup a database that adheres to the predefined structure by adding all necessary tables to an empty DB.
You can create all necessary tables by executing the individual scripts in the Database/Scripts directory or execute the combined script containing all statements.

Afterwards, please enter the credentials of your DB in the config object at `./Database/db_repository.py`.  

If you are interested in working with the data previously obtained in our work, you can find a mysql dump of the populated database at https://figshare.com/s/4dd1130c336f43f6e18c.

### CVE Search
As direct and public lookups into the public CVE databases come with multiple difficulties, this project works on a local copy of CVEs and CPEs in order to obtain the relevant data.
Please make sure the machine you are executing our tools on has the cve-search tool installed and running. 
We ask you not to change the default name and access policy of the respective mongo db.

Find the latest version of cve-search at:
https://github.com/cve-search/cve-search

### Libraries
The root directory contains a `requirements.txt` with all the necessary pip install statements for your convenience.

### Local clone of source repositories
In order to perform any repository mining or vulnerability age calculations you will require a local clone of the project's
repository you want to work with.

## Mapping CVEs to fixing commits

The functionality for evaluating mapping approaches and collecting mapping information is provided as command line interface in `vcc_mapper.py`
.
<br>For example the command `python vcc_mapper.py -d  openssl` would extract all mappings between CVEs and 
fixing commits for OpenSSL and store all of the information in the database. 
Execute `python vcc_mapper.py -h` for more information.

### Configuration
All information required to perform mappings is provided via a XML configuration file. 

#### Config codes
During all steps in any of the provided tools different projects are identified using a unique config or product code. 
Please make sure that these remain unique if you introduce new ones.
You can get list of all config codes that have cve entries in the DB for by executing this SQL statement.

`SELECT DISTINCT(config_code)
 FROM cve_config_code`

#### XML structure
The config.xml is structured as follows:
<br> Under the root node you can specify multiple `<product>` nodes each identified by the attribute `name` that is their config code.

For each product you may specify multiple `<mapping>` nodes each representing one mapping approach. Keep in mind that 
each node will trigger the mining process of the NVD and the repository anew.
A mapping node has to specify its `<type>`. Currently, 3 native mapping types are supported:
 1. <b>TypeCVEID:</b> The CVE-IDs of associated CVEs are extracted directly from the commit message
 2. <b>TypeCommitSha:</b> The references of the CVE contains a link to the fixing commit from which the commits sha can 
 be extracted
 3. <b>TypeCommonID:</b> Both the CVE references and the commit messages contain common identifiers, like those of a 
 bug/issue tracking system

You may add mappings obtained by different means (e.g. third parties) by calling the `map_to_list` method of 
`VCCMappings/RepoInspection` with your own mapping list and XML Element. 

The `<mapping>` node requires at least one `<nvd>` and `<repo>` node specifying which CVEs to look into and the source 
code location. Both require (may depend on the mapping type) a `<regex-list>` node that contains regular expressions to
extract the necessary information from the CVE references and commit messages. Take a look at the `config.xml` provided
by us for examples.

#### Our configuration
The provided `config.xml` contains the configuration used by us to create major part of our mapping database. 
Please note that only the mapping approaches for the projects we referred to in our paper have been empirically evaluated.
<br>This configuration may contain some preliminary mapping approaches for the other projects that may lead to incorrect mappings. 
 
## Lifetime Estimation

The functionality for estimating vulnerability lifetimes is implemented as CLI in `lifetime_estimation.py`. 
An examplary excecution of the tool could look like this: 
<br> `python ./lifetime_estimation.py -p -he=vuldigger2 --delimiter=,  openssl`. 
<br> To the all possible flags execute `python ./lifetime_estimation -h`.


The tool relies on the database described above to gather mappings for the defined product key. 
The tool also assumes that the config.xml contains a respective `<product>` with at least one mapping to extract the 
repository location from. 

### Heuristics
You can use different heuristics to estimate the vulnerability lifetime. 
* A best effort reimplementation of the VCCFinder heuristic introduced by Perl et al. [[1]](#references)
* A best effort reimplementation of the VulDigger heuristic [[2]](#references)
* Our own heuristic, which is referred to als VulDigger2

The heuristic is set by the required parameter `--he`. <br>
You may also implement you own heuristic by inheriting from the HeuristicInterface in 
`/Heuristics/HeuristicInterface.py` and adjusting the cli accordingly. 

### Output
The tool generates a csv file with 1 entry per CVE and fixing commit containing the following data.
* CVE-ID as well as CWE-ID, CVSS-Score and CVSS-Vector
* Sha of the fixing commit and its commit date 
* Sha of the most-blamed commit, newest and oldest of the blamed commits and ther commit dates
* Average and weighted average date over the commit dates of all blamed commits
* Number of commits on the working tree between the fixing commit and the most-blamed, newest and oldest commit as well
as the weighted-averaged commit date
* Sha and commit data of the actual VCC if you specified a ground truth file
* Information if the CVE effected a Debian stable version, if you set the `-d` flag

The path of the output file may be change using the `-o` flag.


### Ground truth
You may provide a ground truth file that contains mappings between VCCs, Fixing Commits and CVEs. 
The tools expects the data to be in that order separated by two whitespaces and with one header line. 
However, the tool still requires the database to be populated with the CVEs in the ground truth file to obtain
additional information like CWE, CVSS, etc.

### Runtime 
Depending on the number of mappings and the size and complexity of the repository the data collection process may run 
for a few hours, especially since the mappings are processed in a serial fashion. <br>
Parallelising our code could provide an existential speed up, but we did not deem it worth the effort since the data 
collection has to be only executed once for each project in the entire evaluation process. 

## Authors
* Manuel Brack - Initial work - [manuelbrack](https://github.com/manuelbrack)
* Jan Philipp Wagner - Initial work - [jpwagner](https://github.com/jp-wagner)

## References

[1] Henning Perl, Sergej Dechand, Matthew Smith, Daniel
    Arp, Fabian Yamaguchi, Konrad Rieck, Sascha Fahl,
    and Yasemin Acar. Vccfinder: Finding potential vulnerabilities
    in open-source projects to assist code audits.
    In Proceedings of the 22nd ACM SIGSAC Conference
    on Computer and Communications Security, pages 426–
    437, 2015.

[2] Limin Yang, Xiangxue Li, and Yu Yu. Vuldigger: A justin-
    time and cost-aware tool for digging vulnerabilitycontributing
    changes. In GLOBECOM 2017-2017 IEEE
    Global Communications Conference, pages 1–7. IEEE,
    2017.
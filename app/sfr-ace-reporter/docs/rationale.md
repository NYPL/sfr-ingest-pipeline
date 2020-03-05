# Background on Daisy Ace, AWS Lambda and Chromium

This service runs on an EC2 instance and can be accessed via an API. It has been configured this way to handle the dependencies and interactions that arise between these three components

## Daisy Ace

The [EPUB Accessibility report generator](https://daisy.github.io/ace/) was designed as a command-line tool only, without documented support for use as a npm package in another project (though it is written in node.js). In order to use it for this service (on demand in response to a Kinesis stream) it was necessary to use it as a package. The Report generator works by splitting a zipped EPUB file into its component parts and reading them in part, by loading them into a headless Chromium instance. This then generates a block of JSON data which can be returned via API for the rest of the data ingest process.

## AWS Lambda

The main components of the ResearchNow data ingest pipeline are running in Lambda instances to allow for an easily scaleable and maintainable pipeline. The function that takes EPUB files and stores them in S3 takes the zipped EPUB files, explodes them into their components and stores them as both zipped and exploded versions. This runs smoothly but encounters several problems.

First, the package size of Lambdas is generally limited to 50MB for the most common upload methods. Including the Ace Report tool in this Lambda increased the size of the package to 200MB+ due to various dependencies. This could be mitigated by uploading the package via S3, however that is not ideal from a maintainability standpoint.

Second, the startup time of the Lambda is severly affected by inlcuding the Ace Reporting tool. It adds several seconds to the startup of each Lambda instance (largely due to Chromium) and its use is therefore generally not encouraged. One of the main reasons an ec2 instance was created was because it is always available and eliminates the need for startup on each call.

## Chromium

As a dependency of the Ace Reporter Chromium adds over 80MB in requirements. Additionally, depending on the flavor of linux it is being deployed on it may be missing several key libraries (mainly libX and its dependencies), which complicates deployment in many enviroments. There are several projects to create node and/or Lambda centric distributions of Chromium, which may provide a path forward for future work to incorporate these tools into a Lambda.

## EC2 Size/Responsiveness

As it stands now this service is running on a t3.small ec2 instance. This was selected as the t3 instances offer more vCPU cores at lower levels than the standard t2 instances. This allows for better parallel performance as multiple EPUBs can be processed at once (ideally having a 3+ core machine would process a full batch in parallel, but having 2 cores seems to work well at the moment). The Ace Report tool is also somewhat of a memory hog, and it would perhaps improve processing time if additional memory was provisioned. However, that has not been done yet out of caution, it can be increased at any time.

## Future Work

There are several potential solutions to these questions. The most comprehensive would be to either eliminate the Chromium dependency of the Ace Reporting tool, however that seems unlikely as it is a key part of their reporting tool. Replacing it with a Lambda compatible Chromium package is perhaps more feasible and will be on the To-Do list for future tasks.

Fine tuning the ec2 instance for performance/cost is another option as having a standalone API offers several advantages, such as being able to initiate/generate Accessibility Reports from arbitrary points in the ResearchNow pipeline. For example, an automated tool that updates/fixes epubs could generate new reports without re-implementing any code around them.

However, implementing this as a standalone Lambda is likely the best of both worlds, and that should be the ultimate goal of this project.

### April 2019 Update

With other tasks involving the data pipeline ongoing, other tools have been evaluated for this task, specifically [EpubCheck](https://github.com/w3c/epubcheck) which is a Java library under active development. This tool was evaluated with an eye to possible deployment as a Lambda function to replace this tool.

However, assessment revealed that the EpubCheck tool is primarily focused on validating ePub files, not on their accessibility, which would necessitate a higher degree of custom development than the ACE tool. At present an update is being made that will account for the speed issues around the ACE tool, allowing it to read from a stream of messages and generate them asynchronously from the general update stream of the data pipeline. While this will work in the medium term, a fully optimized solution should still be considered for future work.

TODO

- Fine tune EC2 instance for performance/cost
- Implement Lambda-compliant Chromium version for fork of @daisy/ace
- Review @daisy/ace for unnecessary packages/dependencies with eye to decreasing size and making Lambda deployments easier
- Implement standalone Lambda for processing/generate Ace Reports given standard in SFR-193 

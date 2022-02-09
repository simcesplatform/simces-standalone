# domain messages

Domain specific Python message classes for the SimCES platform.

## Messages

The following messages have been defined:

- `ResourceStateMessage`
    - Child class of AbstractResultMessage
    - Adds CustomerId, RealPower, ReactivePower, Node and StateOfCharge
    - Definition: [ResourceState](https://simcesplatform.github.io/energy_msg-resourcestate/)
- `PriceForecastStateMessage`
    - Child class of AbstractResultMessage
    - Adds MarketId, ResourceId, PricingType, Prices
    - Definition: [PriceForecastStateMessage](https://simcesplatform.github.io/energy_msg-priceforecaststate/)
    
## How to include domain-messages to your own project

Two optional ways of including domain-messages are described here.

- Manual copy of the domain\_messages folder (not recommended)

    - The easiest way to get the most recent version of the library.
    - No easy way of checking if there are updates for the library code. For a work in progress library this is a significant downside.

    Installation instructions:
    - Clone the domain-messages repository:

        ```bash
        git clone https://github.com/simcesplatform/domain-messages.git
        ```

    - Copy the `domain_messages` folder from domain-messages repository manually to the root folder of your own Python project.
    - Copy the `tools` folder from simulation-tools folder located under domain-messages repository manually to the root folder of your own Python project.
    - Start using the library. For example the ResourceStateMessage class can be made available:

       ```python
       from domain_messages.resource import ResourceStateMessage
       ```

- Using domain-messages as a Git submodule in your own Git repository (recommended)
    - Allows an easy way to update to the newest version of the library.
    - Requires the use of Git repository (some kind of version control is always recommended when working source code).
    - Requires more initial setup than manual copying.
    - For example, static-time-series-resource repository is including the library as a Git submodule.

    Installation instructions:
    - In the root folder of your Git repository add domain-messages as a Git submodule

        ```bash
        # run this from the root folder of your Git repository
        git submodule add -b master https://github.com/simcesplatform/domain-messages.git
        git submodule init
        cd domain-messages
        git submodule init    
        cd simulation-tools
        cd ../..
        git submodule update --remote --recursive
        ```

    - The domain-messages folder should now contain a copy of the domain-messages repository with the library code found in the `domain-messages/domain_messages` folder. Under domain-messages there should also be a copy of the simulation-tools repository in the simulation-tools folder. To enable similar way of importing library modules as is used in the library itself or when using the manual copy of the domain_messages folder, the Python interpreter needs to be told of the location of the tools and domain_messages folders. One way to do this is to use the init code from domain-messages:
        1. Copy the init folder from domain-messages to the root folder of your code repository:

            ```bash
            # run this from the root folder of your Git repository
            cp -r domain-messages/init .
            ```

        2. Include a line `import init` at the beginning of the Python source code file from where your program is started. E.g. if your program is started with `python master.py` or `python -m master` include the import init line at the `master.py` file before any imports from the domain-messages library.
            - Another way to avoid modifying your source code would be to include the import init line in `__init__.py` file
    - Start using the library. For example the ResourceStateMessage class can be made available by using:

       ```python
       from domain_messages.resource import ResourceStateMessage 
       ```

    - To update the domain-messages library to the newest version, run:

        ```bash
        # run this from inside your Git repository (but not from the domain-messages folder)
        git submodule update --remote --recursive
        ```

## How to add support for a new message type as a Python class

See the [simulation-tools readme](https://github.com/simcesplatform/simulation-tools)
for general detailed instructions. Messages related to a certain domain topic can be placed to their own python module under a topic specific pakcage. They can then be imported in the package's \_\_init\_\_.py file to make their importing more convenient. For example the ResourceStateMessage class is located in the resource\_state module in the resource pakcage but it can be used with:

```python
from domain_messages.resource import ResourceStateMessage
```    
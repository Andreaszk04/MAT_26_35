# Summary

**Title:** Understanding IFC Data classification for openBIM Workflows and Tools

**Summary:** An introduction to the IFC data structure (classes, objects, types, properties and quantities) and how it enables openBIM workflows such as IDS and BCF, with essential IfcOpenShell commands for extracting model data when developing tools.

**Relevant roles:** R2 (Analyst), R3 (Manager).

**Focus areas:** Gives a basic understanding of IFC and openBIM for all focus areas.

# Learning objectives

- Being able to comprehend the IFC data structure
- Understanding how IFC faciliates openBIM processes
- Comprehending the concept of openBIM
- Understanding openBIM workflows
- Knowing where to locate model data, to be able to build useful tools

# Introduction

When verifying or solving problems or claims in a project, it is important to understand and to be able to identify the accessible data of the given BIM model. Furthermore, when working as a BIM team consisting of members with different roles, it is also important to understand the structure and reasoning behind the classifications in the model.

At its core openBIM is a process, where the traditional elements of BIM are extended to improve accessibility, usability, collaboration and management of data. Thus facilitating frictionless collaboration between focus areas of a project, and making data verification and management across areas easier. In this course the openBIM process is already implemented in the project models, where IFC classifications is used to extend the usability of the model rather than using traditional BIM programs such as Revit.

### What is IFC

Fundamentally IFC is both a data structure and format. Thus IFC stands as an essential basis when wanting to exchange digital building information. In general a basic IFC file can be opened by any text editor. The IFC file will contain information on the author, the software used and what IFC schema (version) the model is based on. Furthermore the IFC file will contain all data instances in the model, this could be a material with its given properties.

### IFC definitions

![IFC definitions](images/image1.png)

The IFC data structure contains different definitions, that differ from each other.

**Class:** Class can also be referred to as entity, element class or entity type. An entity is a class of information defined by common attributes and constraints.

**Object:** Also referred to as instance, specimen and entity instance. An object can either be a physical or a conceptual instance. For example a wall would be a physical object, but a room would be a conceptual object.

**Object type:** Object type is similar to classes. It is a classification that combines several common characteristics of several objects/instances, but certain basic parameters are defined by the class. An example could be a specific wall type, which could have certain characteristics shared with other walls of the same object type, but not with the entire wall class.

**Attribute:** Also referred to as parameter. An attribute is some sort of information within a certain class.

**Quantity:** Quantity is a fundamental parameter derived from the physical properties of an object. Possible measurements of quantity could be the length, height and volume of a beam (object).

**Quantity set:** A quantity set is a specific container of quantities assigned to a given object.

**Property:** A property is some sort of information, which could be used to describe the nature of an object. Properties are not constant and can be custom created for a single model.

**Property set:** The property set is similar to the quantity set. It contains specific properties of a object but could be user created (same as properties).

# openBIM workflows using IFC

![openBIM workflows](images/image2.png)

Since all entities in a project are quantified as data in the IFC file, it facilitates different openBIM processes, such as:

### Information Delivery Specification (IDS)

IDS makes use of the IFC data to validate requirements and standards of the model. Simply using code to check the data, it is much easier to validate whether for example all objects have been assigned a material.

### BIM Collaboration Format (BCF)

BCF is a standard communication protocol for efficient problem/issue management. Instead of receiving corrections from the project manager, BCF in collaboration with IDS makes use of the IFC data, to precisely refer to entities with issues, and assigning responsibility to the relevant project member. Ultimately BCF gives the project manager better ways to communicate issues and a like with relevant responsible members of a project.

## Creating tools with IFC

With the basic understanding of the data structure of IFC, it becomes more transparent what data is accessible. Comprehending this facilitates a more approachable process, when developing and outlining the use case of tools.

In practice, classification is what makes these things possible. The most useful IfcOpenShell commands to explore a model are shown below (importing the model is not shown).

| Command | What it returns |
|---|---|
| `model.schema` | Version/schema of the IFC file. |
| `model.by_type("IfcWall")` | All elements of a class, e.g. all walls when using `IfcWall`. |
| `entity.get_info()` | Direct attributes such as `Name`, `ObjectType` etc. of an *entity*. |
| `Element.get_psets(entity)` | All property and quantity sets of an *entity*. |
| `Element.get_material(entity)` | Material or layer set of an *entity*. |
| `Element.get_type(entity)` | The type of an *entity*. |
| `Element.get_types(type)` | All occurrences of a *type*, e.g. a specific `IfcWallType`. |
| `Element.get_container(entity)` | The spatial container of an *entity*, e.g. its storey. |

The IFCopenshell commands above are the most basic ways to extract data from the model. Using the commands and thereby checking what data is actually available in the model, should be the first step in outlining what tools are possible to build.

Furthermore the tool developers should reflect on how the tool could fit into an existing or future openBIM workflow. Questions that could be adressed could be: What member of the project should be the user? How can the tool improve collaboration? How can the project manager validate the outputs/results from the tool? What new tools could be developed on top of the tool? And how could the tool in participation with other tools solve or help answer broader claims or issues?

# Sources

- *BIMcert Handbook 2023* – sections 2.3.2 and 3.8 (bSDD), 3.7 (IDS, Classification facet).
- buildingSMART International – *openBIM Definition*.

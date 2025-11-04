# Research 

Create a deep understanding of the `Request` and how it works. Follow the `Instructions` to create the `Report` and explain it in a way that is very simple to understand. 

## Instructions
- IMPORTANT: You are not trying to solve, you are trying to understand how the `Request` works. 
- IMPORTANT: Do not assume anything. If you dont know, then research. 
- Create the `Research Report` in the `specs/` directory with filename: `research-{slugified-title}.md`
- Follow the `Examples` For more detail. 
- Research the codebase to understand existing patterns, architecture, and conventions before planning the feature.
- Use your reasoning model: THINK HARD about the how this `Request` works and its design.
- Focus on the `Request` and do not deviate. 
- Don't use decorators. Keep it simple.


## Research Report 
```md
# Request
 <request from user>

## Request Description
<describe the Request in detail, including its purpose and value to users>

## Relevant Files
<find and list the files that are relevant to your research and the users `request`>

## Inputs 
<What is needed to trigger the `Request`, what format is it expected on?>

## Outputs
<Where is this being used? what format does it have to be on to be able to connect properly? >

## Notes
<optionally list any additional notes or context that are relevant to the bug that will be helpful to the developer>
```

## Examples
- If we are asked to research how the agent search tool works. We would need to understand what are all the variables that can trigger this. Where do they come from? Where do they go? What needs to be right for it to work correctly? 

## Report out in terminal
Provide a concise outline:

**Entry Point:** Where it starts (Frontend/Backend, file:line)
**Key Processing Steps:** 3-5 bullet points of major stages
**Assembly Point:** Where inputs come together (file:line)
**Output Destination:** Where it ends (Frontend/Backend, file:line)
**Key Files:** Top 5 most important files with roles



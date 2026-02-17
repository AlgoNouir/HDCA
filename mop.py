from models.llm import response_llm, parse_json


class_template = '''
from ..mop import MopAgent

class {class_name}(MopAgent):
    """{class_desc}"""

    ENTITY_NAME = "{class_entity}"
'''


function_template = '''
    def {function_name}(self, {function_args}):
        """
        {function_desc}
        """

        return """{function_prompt}"""
'''


# ----------------------------------------------------- AGENT


class MopAgent:

    ENTITY_NAME = ""

    def __init__(self, prompt):
        self.first_prompt = prompt

    def think(self, prompt):
        """this function checks this act exists or not"""

        # Calculate actions from public methods (not starting with _)
        actions = {}
        for name in dir(self.__class__):
            if not name.startswith('_') and name != '__init__' and callable(getattr(self.__class__, name, None)):
                method = getattr(self.__class__, name)
                if hasattr(method, '__doc__') and method.__doc__:
                    actions[name] = method.__doc__.strip()
                else:
                    actions[name] = ""

        # serialize actions
        actions = '\n\n'.join([f"### {act}\n{value}" for act, value in actions.items()])

        # Calculate status from class properties and values
        status = {}
        for name, value in vars(self.__class__).items():
            if not name.startswith('_') and not callable(value):
                status[name] = value

        # serialize status
        status = '\n'.join([f"- {stat}: {value}" for stat, value in status.items()])

        # get response from LLM
        response = response_llm(
            "",
            main_desc=self.__doc__,
            model_status=status,
            actions_list=actions,
            prompt=prompt,
        )

        # {
        #    "finish": false | true, 
        #    "exists": false | true, 
        #    "name": "NAME OF FUNCTION",
        #    "description": "DESCRIPTION OF FUNCTION",
        #    "args": [
        #        ...
        #        { "name": "ARGS NAME", "value": "VALUE", "description": "DESCRIPTION OF ARGS" },
        #        ...
        #    ]
        # }

        function_exists = response.get("exists", False)
        function_name = response.get("name", "")
        function_desc = response.get("description", "")
        function_args = response.get("args", {})

        # check is finished
        if function_name == "response_user":
            return function_args.get("response", {}).get("value", None)

        # run new action and update the prompt
        if function_exists:
            act_response = self._act(
                prompt=prompt,
                name=function_name,
                desc=function_desc,
                args=function_args,
            )

            prompt += act_response

        # add new action to class        
        else:
            self._add_action(
                prompt=prompt,
                name=function_name,
                desc=function_desc,
                args=function_args,
            )

        # think again with new function
        return self.think(prompt)

    def _add_action(self, prompt, name, desc, args):
        """
        this function create new action to instance, 
        and after that call think again
        """
        
        # add args to desc
        if len(args) > 0:
            desc += "\t\tArgs:"
            desc += '\n'.join([
                f'\t\t\t{arg.get("name")}: {arg.get("description")}' 
                for arg in args
            ])

        # ask LLM about new prompt
        response = response_llm(
            "./prompts/add-action.md",
            name=name,
            prompt=desc,
        )

        # create new func
        new_func = function_template.format(
            function_name=name,
            function_desc=desc,
            function_args=", ".join([f'{a.get("name")}' for a in args]),
            function_prompt=response.get("text"),
        )

        # add function to file
        with open(f"./agents/{self.ENTITY_NAME}.py" ,"a") as file:
            file.write(new_func)

        # update himself
        ...

    def _act(self, prompt, name, desc, args):

        func = self.__getattribute__(name)
        func_response_prompt = func(**args)

        response = response_llm(
            "./prompts/action.md",
            what=prompt,
            why=desc,
            how=func_response_prompt
        )

        return response


class GodAgent(MopAgent):

    def create_entity(self, prompt):
        """response a entity and create a agent"""


        # load template
        with open("./prompts/system.md", "r") as f:
            template = f.read()

        system_prompt = template.format()
        response = parse_json(response_llm(system_prompt))

        entity_name: str = response.get("name")
        entity_desc: str = response.get("desc")

        # write default class
        with open(f"./agents/{entity_name}.py") as f:
            f.write(class_template.format(
                class_name = entity_name.capitalize(),
                class_desc = entity_desc,
                class_entity = entity_name
            ))

        return 


watcher = MopAgent("""
we have a cat and dog on world.
if this cat and dog married togheter,
what is type of they child ?
""")


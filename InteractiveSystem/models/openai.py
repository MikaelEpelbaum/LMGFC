import functools
import os
import re
import threading

import httpx as _httpx
import ida_kernwin
import openai

from InteractiveSystem.models.base import LanguageModel
import InteractiveSystem.config

_ = InteractiveSystem.config.translate.gettext


class GPT(LanguageModel):
    def __init__(self, model):
        self.model = model
        # Get API key
        if not InteractiveSystem.config.parsed_ini.get('OpenAI', 'API_KEY'):
            api_key = os.getenv("OPENAI_API_KEY")
        else:
            api_key = InteractiveSystem.config.parsed_ini.get('OpenAI', 'API_KEY')
        if not api_key:
            print(_("Please edit the configuration file to insert your OpenAI API key!"))
            raise ValueError("No valid OpenAI API key found")

        # Get OPENAPI proxy
        if not InteractiveSystem.config.parsed_ini.get('OpenAI', 'OPENAI_PROXY'):
            proxy = None
        else:
            proxy = InteractiveSystem.config.parsed_ini.get('OpenAI', 'OPENAI_PROXY')

        # Get BASE_URL
        if not InteractiveSystem.config.parsed_ini.get('OpenAI', 'BASE_URL'):
            base_url = None
        else:
            base_url = InteractiveSystem.config.parsed_ini.get('OpenAI', 'BASE_URL')

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=_httpx.Client(
                proxies=proxy,
            ) if proxy else None
        )

    def __str__(self):
        return self.model

    def query_model(self, query, cb=None, additional_model_options=None):
        """
        Function which sends a query to gpt-3.5-turbo or gpt-4 and calls a callback when the response is available.
        Blocks until the response is received
        :param query: The request to send to gpt-3.5-turbo or gpt-4
        :param cb: The function to which the response will be passed to.
        :param additional_model_options: Additional parameters used when creating the model object. Typically, for
        OpenAI, response_format={"type": "json_object"}.
        """
        if additional_model_options is None:
            additional_model_options = {}
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": query}
                ],
                **additional_model_options
            )
            if cb:
                ida_kernwin.execute_sync(functools.partial(cb, response=response.choices[0].message.content),
                                         ida_kernwin.MFF_WRITE)
            else:
                return response.choices[0].message.content
        except openai.BadRequestError as e:
            # Context length exceeded. Determine the max number of tokens we can ask for and retry.
            m = re.search(r'maximum context length is \d+ tokens, however you requested \d+ tokens', str(e))
            if m:
                print(_("Unfortunately, this function is too big to be analyzed with the model's current API limits."))
            else:
                print(_("General exception encountered while running the query: {error}").format(error=str(e)))
        except openai.OpenAIError as e:
            print(_("{model} could not complete the request: {error}").format(model=self.model, error=str(e)))
        except Exception as e:
            print(_("General exception encountered while running the query: {error}").format(error=str(e)))

    def query_model_async(self, query, cb, additional_model_options=None):
        """
        Function which sends a query to {model} and calls a callback when the response is available.
        :param query: The request to send to {model}
        :param cb: To function to which the response will be passed to.
        :param additional_model_options: Additional parameters used when creating the model object. Typically, for
        OpenAI, response_format={"type": "json_object"}.
        """

        if additional_model_options is None:
            additional_model_options = {}
        print(_("Request to {model} sent...").format(model=str(InteractiveSystem.config.model)))
        t = threading.Thread(target=self.query_model, args=[query, cb, additional_model_options])
        t.start()

    # -----------------------------------------------------------------------------

    def query_model_sync(self, query, additional_model_options=None):
        """
        Function which sends a query to {model} and returns the response when available.
        :param query: The request to send to {model}
        :param additional_model_options: Additional parameters used when creating the model object. Typically, for
        OpenAI, response_format={"type": "json_object"}.
        :return: Response from the model.
        """
        print("in query_model_sync")
        if additional_model_options is None:
            additional_model_options = {}
        print(_("Request to {model} sent...").format(model=str(InteractiveSystem.config.model)))

        # Call query_model directly instead of starting a new thread
        return self.query_model(query, additional_model_options=additional_model_options)

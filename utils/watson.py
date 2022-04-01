import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions, SyntaxOptions, SyntaxOptionsTokens
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import env


# Authentication via IAM
auth = IAMAuthenticator(env.IBM_API_KEY)
SERVICE = NaturalLanguageUnderstandingV1(
    version='2021-08-01',
    authenticator=auth
)
SERVICE.set_service_url(env.IBM_API_URL)


def send_nlp_request(message):
    response = SERVICE.analyze(
        text = message,
        features = Features(
            entities=EntitiesOptions(),
            keywords=KeywordsOptions(),
            syntax=SyntaxOptions(tokens=SyntaxOptionsTokens(
                part_of_speech=True,
                lemma=True,
            )),
        )
    ).get_result()
    return response


def get_main_entity(nlp_resp):
    if len(nlp_resp['entities']) > 0:
        return nlp_resp['entities'][0]['text']
    elif len(nlp_resp['keywords']) > 0:
        return nlp_resp['keywords'][0]['text']


def get_tokens(nlp_resp):
    return nlp_resp['syntax']['tokens']
"""See available models in the Ersilia Model Hub"""

import subprocess
import requests
import os
from .card import ModelCard
from .. import ErsiliaBase
from ..utils.paths import Paths
from ..auth.auth import Auth
from ..default import GITHUB_ORG

try:
    import webbrowser
except ModuleNotFoundError as err:
    webbrowser = None

try:
    import pandas as pd
except ModuleNotFoundError as err:
    pd = None

try:
    from github import Github
except:
    Github = None

try:
    from tabulate import tabulate
except:
    tabulate = None


class ModelCatalog(ErsiliaBase):

    def __init__(self, config_json=None, as_dataframe=True):
        ErsiliaBase.__init__(self, config_json=config_json)
        self.as_dataframe = as_dataframe
        self.eos_regex = Paths._eos_regex()

    def _is_eos(self, s):
        if self.eos_regex.match(s):
            return True
        else:
            return False

    def _return(self, df):
        if self.as_dataframe:
            return df
        h = list(df.columns)
        R = []
        for r in df.values:
            R += [r]
        return tabulate(R, headers=h)

    @staticmethod
    def spreadsheet():
        """List models available in our spreadsheets"""
        if webbrowser:
            webbrowser.open("https://docs.google.com/spreadsheets/d/1WE-rKey0WAFktZ_ODNFLvHm2lPe27Xew02tS3EEwi28/edit#gid=1723939193") # TODO: do not just go to the website

    def github(self):
        """List models available in the GitHub model hub repository"""
        token = Auth().oauth_token()
        if token:
            g = Github(token)
            repo_list = [i for i in g.get_user().get_repos()]
            repos = []
            for r in repo_list:
                owner, name = r.full_name.split("/")
                if owner != GITHUB_ORG:
                    continue
                repos += [name]
        else:
            repos = []
            url = "https://api.github.com/users/{0}/repos".format(GITHUB_ORG)
            results = requests.get(url).json()
            for r in results:
                repos += [r["name"]]
        models = []
        for repo in repos:
            if self._is_eos(repo):
                models += [repo]
        return models

    def hub(self):
        """List models available in Ersilia model hub repository"""
        mc = ModelCard()
        models = self.github()
        R = []
        for model_id in models:
            card = mc.get(model_id)
            if card is None:
                continue
            R += [[model_id, card["title"]]]
        if pd:
            df = pd.DataFrame(R, columns=["MODEL_ID", "TITLE"])
            return self._return(df)
        else:
            return R

    def local(self):
        """List models available locally"""
        mc = ModelCard()
        R = []
        for model_id in os.listdir(self._bundles_dir):
            card = mc.get(model_id)
            R += [[model_id, card["title"]]]
        if pd:
            df = pd.DataFrame(R, columns=["MODEL_ID", "TITLE"])
            return self._return(df)
        else:
            return R

    def bentoml(self):
        """List models available as BentoServices"""
        result = subprocess.run(['bentoml', 'list'], stdout=subprocess.PIPE)
        result = [r for r in result.stdout.decode("utf-8").split("\n") if r]
        if len(result) == 1:
            return
        columns = ["BENTO_SERVICE", "AGE", "APIS", "ARTIFACTS"]
        header = result[0]
        values = result[1:]
        cut_idxs = []
        for col in columns:
            cut_idxs += [header.find(col)]
        R = []
        for row in values:
            r = []
            for i, idx in enumerate(zip(cut_idxs, cut_idxs[1:]+[None])):
                r += [row[idx[0]:idx[1]].rstrip()]
            R += [r]
        if pd:
            df = pd.DataFrame(R, columns=columns)
            df["MODEL_ID"] = [x.split(":")[0] for x in list(df["BENTO_SERVICE"])]
            df = df[["MODEL_ID"]+columns]
            return self._return(df)
        else:
            return R

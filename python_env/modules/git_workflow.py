import subprocess
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

class GitWorkflow:
    """
    Gère les opérations Git pour le dépôt du projet.
    """
    def __init__(self, config_manager):
        self.config = config_manager
        self.target_branch = self.config.get('git.branch', 'dev')

    def _run_git_command(self, command_args):
        """
        Exécute une commande Git et gère les erreurs.
        """
        cmd = ["git"] + command_args
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                logging.info(f"Sortie Git : {result.stdout.strip()}")
            if result.stderr:
                logging.warning(f"Erreurs/Avertissements Git : {result.stderr.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Échec de la commande Git '{' '.join(cmd)}' : {e.stderr.strip()}")
            return False
        except FileNotFoundError:
            logging.error("La commande 'git' n'a pas été trouvée. Assurez-vous que Git est installé.")
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors de l'exécution de Git : {e}")
            return False

    def check_branch(self):
        """
        Vérifie si la branche actuelle est la branche cible.
        """
        logging.info(f"Vérification de la branche Git actuelle. Branche cible : '{self.target_branch}'")
        try:
            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=True, capture_output=True, text=True)
            current_branch = result.stdout.strip()
            if current_branch == self.target_branch:
                logging.info(f"La branche actuelle est '{current_branch}', ce qui correspond à la branche cible.")
                return True
            else:
                logging.error(f"La branche actuelle est '{current_branch}', mais la branche cible est '{self.target_branch}'.")
                return False
        except subprocess.CalledProcessError as e:
            logging.error(f"Impossible de déterminer la branche Git actuelle : {e.stderr.strip()}")
            return False

    def commit_and_push_changes(self, message="chore(dev): agent bootstrap/update"):
        """
        Ajoute, committe et pousse les changements vers la branche cible.
        """
        logging.info("Ajout de tous les fichiers modifiés/nouveaux à Git.")
        if not self._run_git_command(["add", "-A"]):
            return False
        
        logging.info(f"Création du commit avec le message : '{message}'")
        if not self._run_git_command(["commit", "-m", message]):
            # Si aucun changement à committer, la commande commit échouera.
            # Vérifier si l'erreur indique "nothing to commit"
            try:
                subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                if "nothing to commit" in e.stderr.lower():
                    logging.info("Aucun changement à committer.")
                    return True # Considérer comme un succès si rien à committer
                else:
                    logging.error(f"Échec du commit Git : {e.stderr.strip()}")
                    return False
            except Exception as e:
                logging.error(f"Erreur inattendue lors du commit Git : {e}")
                return False
        
        logging.info(f"Push des changements vers 'origin/{self.target_branch}'")
        if not self._run_git_command(["push", "origin", self.target_branch]):
            return False
        
        logging.info("Changements Git poussés avec succès.")
        return True

# Exemple d'utilisation (pour les tests)
if __name__ == "__main__":
    from config_manager import ConfigManager
    
    # Créer un fichier config.yaml temporaire pour le test
    temp_config_content = """
    git:
      branch: "dev"
    """
    with open('temp_config.yaml', 'w') as f:
        f.write(temp_config_content)

    # Initialiser un dépôt Git temporaire pour le test
    os.makedirs('temp_repo', exist_ok=True)
    os.chdir('temp_repo')
    subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "dev"], check=True, capture_output=True, text=True)
    with open('test_file.txt', 'w') as f:
        f.write("Initial content")
    subprocess.run(["git", "add", "test_file.txt"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True, text=True)
    # Simuler une remote
    subprocess.run(["git", "remote", "add", "origin", "https://github.com/test/test.git"], check=True, capture_output=True, text=True)


    try:
        config_mgr = ConfigManager(config_path='../temp_config.yaml')
        git_workflow = GitWorkflow(config_mgr)

        print("\nTest de vérification de la branche...")
        print(f"Branche correcte : {git_workflow.check_branch()}")

        print("\nModification d'un fichier et test de commit/push...")
        with open('test_file.txt', 'a') as f:
            f.write("\nAdded new line.")
        
        # Le push échouera car la remote n'est pas réelle, mais le commit devrait fonctionner
        print(f"Commit et push réussis (le push échouera pour le test) : {git_workflow.commit_and_push_changes()}")

    except Exception as e:
        logging.error(f"Erreur lors du test de GitWorkflow: {e}")
    finally:
        os.chdir('..')
        if os.path.exists('temp_config.yaml'):
            os.remove('temp_config.yaml')
        if os.path.exists('temp_repo'):
            subprocess.run(["rm", "-rf", "temp_repo"], check=True, capture_output=True, text=True)

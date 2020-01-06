FROM jupyter/scipy-notebook

USER root

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER && \
    apt update && \
    apt-get install curl -y

ENV PYTHONPATH "${PYTHONPATH}:/home/jovyan/work/q_pack"
    
CMD ["jupyter", "notebook", "--no-browser","--NotebookApp.token=''","--NotebookApp.password=''", "--allow-root"]


# Another way to give root access without password in the compose
    # environment:
    #   GRANT_SUDO: "yes"
    # user:
    #   "root"
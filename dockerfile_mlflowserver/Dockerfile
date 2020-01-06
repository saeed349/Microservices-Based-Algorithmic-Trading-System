# FROM python:3.7
FROM continuumio/miniconda

MAINTAINER Wilder Rodrigues (wilder.rodrigues@ekholabs.ai)

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

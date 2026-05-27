from __future__ import annotations
 
import re
from pathlib import Path
from typing import Any
 
 
CLASS_PATTERN = r'class\s+(\w+)'
METHOD_PATTERN = r'(?:public|private|protected|async|static).*?\s+(\w+)\('
IDENTIFIER_PATTERN = r'\b[A-Z][A-Za-z0-9_]+\b'
ANNOTATION_PATTERN = r'@\w+'
IMPORT_PATTERN = r'import\s+([^;]+)'
 
 
# ---------- helpers ----------
 
def _extract_patch_text(pr_files:list[dict])->str:
 
    patches=[]
 
    for f in pr_files:
        patches.append(f.get("patch", ""))
 
    return "\n".join(patches)
 
 
# ---------- Step 1 + 2 ----------
 
def extract_changed_symbols(pr_files:list[dict])->dict:
 
    patch=_extract_patch_text(pr_files)
 
    classes=re.findall(CLASS_PATTERN,patch)
 
    methods=re.findall(METHOD_PATTERN,patch)
 
    identifiers=re.findall(IDENTIFIER_PATTERN,patch)
 
    annotations=re.findall(ANNOTATION_PATTERN,patch)
 
    imports=re.findall(IMPORT_PATTERN,patch)
 
    return {
        "classes":list(set(classes))[:20],
        "methods":list(set(methods))[:20],
        "identifiers":list(set(identifiers))[:50],
        "annotations":list(set(annotations))[:20],
        "imports":list(set(imports))[:20]
    }
 
 
# ---------- Step 3 ----------
 
def build_dependency_context(
    pr_files:list[dict],
    context_files:list[dict]
)->dict:
 
    symbols=extract_changed_symbols(pr_files)
 
    search_entities=(
        symbols["classes"]+
        symbols["identifiers"]
    )
 
    called_by=[]
    references=[]
 
    for ctx in context_files:
 
        content=ctx.get("content","")
 
        for entity in search_entities:
 
            if entity in content:
 
                called_by.append(
                    ctx.get("path")
                )
 
        imports=re.findall(
            IMPORT_PATTERN,
            content
        )
 
        references.extend(imports)
 
 
    return {
        "relatedFiles":list(set(called_by))[:10],
        "imports":list(set(references))[:20]
    }
 
 
# ---------- Step 4 ----------
 
def retrieve_related_context(
    pr_files,
    context_files
):
 
    symbols=extract_changed_symbols(pr_files)
 
    entities=(
        symbols["classes"]+
        symbols["identifiers"]
    )
 
    retrieved=[]
 
    for file in context_files:
 
        content=file.get("content","")
 
        score=0
 
        for e in entities:
            if e in content:
                score+=1
 
        if score>0:
 
            retrieved.append({
                "path":file["path"],
                "score":score,
                "snippet":content[:1500]
            })
 
    retrieved=sorted(
        retrieved,
        key=lambda x:x["score"],
        reverse=True
    )
 
    return retrieved[:5]
 
 
# ---------- Step 6 ----------
 
def retrieve_related_configs(
        pr_files,
        context_files
):
 
    retrieved=[]
 
    for file in context_files:
 
        name=file.get(
            "path",
            ""
        ).lower()
 
        if (
            "config" in name
            or ".yml" in name
            or ".yaml" in name
            or ".properties" in name
        ):
 
            retrieved.append({
                "path":file["path"],
                "snippet":file.get(
                    "content",
                    ""
                )[:1500]
            })
 
    return retrieved[:5]
 
 
# ---------- Step 7 ----------
 
def extract_endpoint_structure(
        pr_files
):
 
    patch=_extract_patch_text(pr_files)
 
    annotations=re.findall(
        ANNOTATION_PATTERN,
        patch
    )
 
    paths=re.findall(
        r'\("([^"]+)"\)',
        patch
    )
 
    endpoints=[]
 
    for i,p in enumerate(paths):
 
        endpoints.append({
            "annotation":annotations[i] if i<len(annotations) else None,
            "path":p
        })
 
    return endpoints[:10]
 
 
# ---------- Step 8 ----------
 
def extract_observability_signals(
        pr_files,
        context_files
):
 
    patch=_extract_patch_text(pr_files)
 
    terms=[
        "log",
        "metric",
        "trace",
        "monitor",
        "counter"
    ]
 
    findings=[]
 
    for t in terms:
 
        if t.lower() in patch.lower():
            findings.append(t)
 
    imports=re.findall(
        IMPORT_PATTERN,
        patch
    )
 
    findings.extend(imports)
 
    return list(set(findings))[:20]
 
 
# ---------- final ----------
 
def build_production_context(
        pr_files,
        context_files
):
 
    return {
 
        "symbols":extract_changed_symbols(
            pr_files
        ),
 
        "dependencyContext":build_dependency_context(
            pr_files,
            context_files
        ),
 
        "relatedContext":retrieve_related_context(
            pr_files,
            context_files
        ),
 
        "relatedConfigs":retrieve_related_configs(
            pr_files,
            context_files
        ),
 
        "endpointStructures":extract_endpoint_structure(
            pr_files
        ),
 
        "observability":extract_observability_signals(
            pr_files,
            context_files
        )
    }
 
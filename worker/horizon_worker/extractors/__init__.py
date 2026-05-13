"""
Structured-fact extractors that turn ingested article text into rows in
extraction_proposals, then auto-apply high-confidence proposals to the
incident ontology (incident_countries, entities, relationships).

Pipeline:
    case_reports  -->  extractor  -->  extraction_proposals
                                                |
                                                v
                            high-conf + corroborated → auto-apply
                            everything else → analyst-review queue
"""

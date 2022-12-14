% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/utilities_expression.R
\name{getGeneExpression}
\alias{getGeneExpression}
\title{Extract expression values from Seurat object, add stats and format for UI}
\usage{
getGeneExpression(data, genes)
}
\arguments{
\item{data}{Seurat object}

\item{genes}{data.frame of genes of interest, with columns "input" and "name"}
}
\value{
list to send to the UI
}
\description{
Extract expression values from Seurat object, add stats and format for UI
}

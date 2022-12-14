% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/utilities.R
\name{complete_variable}
\alias{complete_variable}
\title{Add NAs to fill variables for filtered cell ids}
\usage{
complete_variable(variable, cell_ids)
}
\arguments{
\item{variable}{vector of values to complete}

\item{cell_ids}{integer vector of filtered cell ids}
}
\value{
NA filled vector, cell_id-complete
}
\description{
This function creates a vector of size max(cell_ids) + 1, with NAs in each
index that corresponds to a filtered cell and the corresponding value in the
ones that were not. It returns the values ordered by cell id by design.
}

#' Subset a Seurat object with the cell ids
#'
#' @param scdata Seurat object
#' @param cells_id Integer vector of cell IDs to keep
#'
#' @return Subsetted Seurat object
#' @export
#'
subsetIds <- function(scdata, cells_id) {
  meta_data_subset <-
    scdata@meta.data[match(cells_id, scdata@meta.data$cells_id), ]
  current_cells <- rownames(meta_data_subset)
  scdata <- subset(scdata, cells = current_cells)
  return(scdata)
}


#' Send cell set to the API
#'
#' This sends a single, new cell set to the API for patching to the cell sets
#' file.
#'
#' @param new_cell_set named list of cell sets
#' @param api_url string URL of the API
#' @param experiment_id string experiment ID
#' @param cell_set_key string cell set UUID
#' @param auth_JWT string authorization token
#'
#' @export
#'
sendCellsetToApi <-
  function(new_cell_set,
           api_url,
           experiment_id,
           cell_set_key,
           auth_JWT) {
    httr_query <- paste0('$[?(@.key == "', cell_set_key, '")]')

    new_cell_set$cellIds <- as.list(new_cell_set$cellIds)

    children <-
      list(list("$insert" = list(index = "-", value = new_cell_set)))

    httr::PATCH(
      paste0(api_url, "/v2/experiments/", experiment_id, "/cellSets"),
      body = list(list(
        "$match" = list(
          query = httr_query,
          value = list("children" = children)
        )
      )),
      encode = "json",
      httr::add_headers(
        "Content-Type" = "application/boschni-json-merger+json",
        "Authorization" = auth_JWT
      )
    )
  }

#' Update the cell sets through the API
#'
#' Used when re-clustering, cell sets are replaced.
#'
#' @param cell_sets_object list of cellsets to patch
#' @param api_url character - api endpoint url
#' @param experiment_id character
#' @param cell_set_key character
#' @param auth_JWT character
#'
#' @export
#'
updateCellSetsThroughApi <-
  function(cell_sets_object,
           api_url,
           experiment_id,
           cell_set_key,
           auth_JWT) {
    httr_query <- paste0("$[?(@.key == \"", cell_set_key, "\")]")

    httr::PATCH(
      paste0(api_url, "/v2/experiments/", experiment_id, "/cellSets"),
      body = list(
        list(
          "$match" = list(query = httr_query, value = list("$remove" = TRUE))
        ),
        list("$prepend" = cell_sets_object)
      ),
      encode = "json",
      httr::add_headers(
        "Content-Type" = "application/boschni-json-merger+json",
        "Authorization" = auth_JWT
      )
    )
  }


#' Ensure is list in json
#'
#' When sending responses as json, Vectors of length 0 or 1 are converted to
#' null and scalar (respectively) Using as.list fixes this, however, long R
#' lists take a VERY long time to be converted to JSON.
#' This function deals with the problematic cases, leaving vector as a vector
#' when it isnt a problem.
#'
#' @param vector
#'
#' @export
#'
ensure_is_list_in_json <- function(vector) {
  if (length(vector) <= 1) {
    return(as.list(vector))
  } else {
    return(vector)
  }
}


#' Add NAs to fill variables for filtered cell ids
#'
#' This function creates a vector of size max(cell_ids) + 1, with NAs in each
#' index that corresponds to a filtered cell and the corresponding value in the
#' ones that were not. It returns the values ordered by cell id by design.
#'
#' @param variable vector of values to complete
#' @param cell_ids integer vector of filtered cell ids
#'
#' @return NA filled vector, cell_id-complete
#' @export
#'
complete_variable <- function(variable, cell_ids) {
  # create correct size vector with NAs, add values ordered by cell_id
  complete_values <- rep(NA_real_, max(cell_ids) + 1)
  complete_values[cell_ids + 1] <- variable
  return(complete_values)
}

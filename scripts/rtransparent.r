repo_base <- file.path(getwd(), "delme_data/")

# Loads required libraries
library(rtransparent)
library(parallel)
library(stringr)

get_indicators <- function(file) {
  tryCatch(
    expr = {
      # Read the content of the TXT file
      txtfile <- file
      ID <- sub("\\.txt$", "", basename(file), ignore.case = TRUE)

      data_code <- rt_data_code(txtfile)
      data_code$article <- ID

      # Return the indicators
      return(c(data_code))
    },
    error = function(e) {
      print(ID)
      print(e)
      return(NULL)
    }
  )
}

# Retrieve the processor cores information OR hardcode it
# num_cores <- detectCores() - 1
num_cores <- 20

# Set working directory
setwd(str_c(repo_base, "txts"))

# List the TXT files
infiles <- dir(pattern = "\\.txt$")

# Starting a cluster which takes in as an argument the number of cores:
cl <- makeCluster(num_cores)
clusterExport(cl, "infiles")
clusterEvalQ(cl, {
  library(rtransparent)
  library(stringr)
})

# Run in parallel with "parLapply"
biglist <- parLapply(cl, infiles, get_indicators)

# Clean out failures
rtransdata <- Filter(function(x) !is.null(x), biglist)

# Stop the cluster
stopCluster(cl)

# Save out final CSV
write.table(
  rtransdata[[1]][!grepl("_[0-9]+$|^fund$|^project$", names(rtransdata[[1]]))],
  file = str_c(repo_base, "data_code_rtransparent.csv"),
  sep = ",",
  row.names = FALSE
)
for (i in 2:length(rtransdata)) {
  write.table(
    rtransdata[[i]][!grepl("_[0-9]+$|^fund$|^project$", names(rtransdata[[i]]))],
    file = str_c(repo_base, "data_code_rtransparent.csv"),
    sep = ",",
    col.names = FALSE,
    row.names = FALSE,
    append = TRUE
  )
}

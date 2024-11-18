repo_base <- file.path(getwd(), "2024_all_ics/")

# loads
library(rtransparent)
library(parallel)
library(stringr)

get_indicators <- function(file) {
  tryCatch(
    expr = {
      # extract and save txt from pdf
      article <- rt_read_pdf(file)
      ID <- sub("\\.pdf$", "", file, ignore.case = TRUE)
      txtfile <- sub("\\.pdf$", ".txt", file, ignore.case = TRUE)
      write(article, txtfile)

      data_code <- rt_data_code(txtfile)
      data_code$article <- ID
      # remove TXT file
      file.remove(txtfile)

      # return the indicators
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

# set working directory
setwd(str_c(repo_base, "pdfs"))

infiles <- dir(pattern = "\\.pdf$")

# Starting a cluster which takes in as an argument the number of cores:
cl <- makeCluster(num_cores)
clusterExport(cl, "infiles")
clusterEvalQ(cl, {
  library(httr)
  library(rtransparent)
  library(stringr)
})

# run in serial with "lapply" OR parallel with "parLapply"
# biglist <- lapply(Filter(function(x) !is.na(x), csvtable$PMID), get_indicators_pmc)
biglist <- parLapply(cl, infiles, get_indicators)

# clean out failures
# rtransdata <- Filter(function(x) length(x) > 8, biglist)
rtransdata <- Filter(function(x) !is.null(x), biglist)

# Syntax Warning: Invalid Font Weight
# Syntax Error (2): Unknown compression method in flate stream
# Syntax Warning: Invalid number of bits needed to represent the difference between the greatest and least number of objects in a page
# Internal Error: xref num 75 not found but needed, try to reconstruct<0a>
# Syntax Warning: Invalid shared object hint table offset
# Syntax Error (7178621): insufficient arguments for Marked Content
# Syntax Error: Couldn't find trailer dictionary
# Syntax Error (316642): Unterminated string
# Syntax Error (316658): End of file inside dictionary
# Syntax Error (315676): Dictionary key must be a name object

# Stop the cluster
stopCluster(cl)
# save out final CSV
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

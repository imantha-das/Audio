using Pkg 
Pkg.activate(joinpath(homedir(),"imanthaWS", "juliaWS", "envs", "jlEnv"))

begin
    using DataFrames 
    using CSV
    using Gadfly, PlotlyJS
    using Cairo
    using TimeSeries
    using Dates
end

function load_data(path::String)
    df = CSV.read(path, DataFrame, header = 1)
    return df
end

function plot_candidates(candidates::DataFrame)
    p = Gadfly.plot(
        candidates,
        x = :name,
        y = :count,
        color = :org,
        Geom.bar
    )
    return p
end



# Run Script ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

begin
    # Load Data 
    df = load_data("data/staff-2021-SGH - Sheet1.csv")
    # Remove last Columns
    df = df[1:end-1,:]
end

begin
    # Rename Columns
    DataFrames.rename!(df, String[
        "date", "session", 
        "spk1_name", "spk1_id", "spk1_mictype", "spk1_org", "spk1_desig",
        "spk2_name", "spk2_id", "spk2_mictype", "spk2_org", "spk2_desig",
        "paid", "amount", "recording_method", "filename", "sharepoint", "duration", "recorded_content", "remarks", "read", "conversational"
    ])

    # Select required Columns
    select!(df, "date", "spk1_name", "spk1_org", "spk1_desig", "spk2_name", "spk2_org", "spk2_desig", "recording_method", "duration", "recorded_content")

    # Drop missing values 
    dropmissing!(df, :duration)

    # Convert Duration to Hours and Minutes
    select!(
        df,
        names(df),
        "duration" => ByRow(x -> Hour(split(x, ":")[1])) => "duration_hrs",
        "duration" => ByRow(x -> Minute(split(x, ":")[2])) => "duration_mins"
    )

    # Convert date to datetime
    df.date = Date.(df.date, "YY-mm-dd")

    # Remove Dates below threshold, last week Sunday
    filter!(x -> x.date < Date(2021, 10,18), df)
end

# Obtain Candidate Names and Recording Count
begin
    spk_names = vcat(df.spk1_name, df.spk2_name) 
    spk_org = vcat(df.spk1_org, df.spk2_org)

    spk_df = DataFrame(Dict(:name => spk_names, :org => spk_org))
    spk_df = combine(groupby(spk_df, Symbol[:name, :org]), nrow => :count) 

    # Filter row containing "-"
    filter!(x -> !(x.name == "-"), spk_df)

    # Plot candidates
    set_default_plot_size(20cm, 15cm)
    p_candidates = plot_candidates(spk_df)

end

t1 = sum(df.duration_hrs) |> Minute
t2 = sum(df.duration_mins) 
int(t1 + t2)


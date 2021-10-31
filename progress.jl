module Progress_Update

export load_data, clean_dataframe, plot_candidates, convert_time, plot_recorded_time, plot_overall_progress, replace_if, plot_recording_method
using Pkg 
Pkg.activate(joinpath(homedir(),"workspace", "julia", "envs", "jlEnv"))

begin
    using DataFrames 
    using CSV
    using Gadfly, PlotlyJS
    using Cairo
    using TimeSeries
    using Dates
end

# Load Data 
# ------------------------------------------------------------------------------------------------------------
@doc """
    Inputs :
        path : Path to CSV file 
    Output : 
        DataFrame
""" ->
function load_data(path::String)
    df = CSV.read(path, DataFrame, header = 1)
    return df
end

# Clean Data
# -----------------------------------------------------------------------------------------------------------
@doc """
    Cleans DataFrame by renaming columns, selecting required columns and Extracting Hours and minutes from Recording Time
    Inputs : 
        df : DataFrame
    Outputs :
        Cleaned Daraframe with selected 
""" ->
function clean_dataframe(df::DataFrame, selected_cols::Array{String})
    # Rename Columns
    DataFrames.rename!(df, String[
        "date", "session", 
        "spk1_name", "spk1_id", "spk1_mictype", "spk1_org", "spk1_desig",
        "spk2_name", "spk2_id", "spk2_mictype", "spk2_org", "spk2_desig",
        "paid", "amount", "recording_method", "filename", "sharepoint", "duration", "recorded_content", "remarks", "read", "conversational"
    ])

    # Remove last Columns
    df = df[1:end-1,:]
        
    # Select required Columns
    select!(df, selected_cols)

    # Drop missing values 
    df = dropmissing(df, :duration)

    # Convert duration to String
    df.duration = Dates.format.(df.duration, "HH:MM:SS")

    # Convert Duration to Hours and Minutes
    select!(
        df,
        names(df),
        "duration" => ByRow(x -> Hour(split(x, ":")[1])) => "duration_hrs",
        "duration" => ByRow(x -> Minute(split(x, ":")[2])) => "duration_mins",
        "duration" => ByRow(x -> Second(split(x,":")[3])) => "duration_secs"
    )

    # Convert date to datetime
    df.date = Date.(df.date, "YY-mm-dd")

    return df
end


# Plot Candidates 
# ---------------------------------------------------------------------------------------------------------------
@doc """
    Plots the number of time each candidate has recordeded 
    Input :
        DataFrame
    Outputs :
        Gadfly Plot
""" -> 
function plot_candidates(df::DataFrame)
    # Concatenate spk1 and spk2 name and organisation columns
    spk_names = vcat(df.spk1_name, df.spk2_name) 
    spk_org = vcat(df.spk1_org, df.spk2_org)

    # Construct a DataFrame and Group based on name and organisation
    spk_df = DataFrame(Dict(:name => spk_names, :org => spk_org))
    spk_df = combine(groupby(spk_df, Symbol[:name, :org]), nrow => :count) 

    # Filter row containing "-"
    filter!(x -> !(x.name == "-"), spk_df)

    # Plot candidates
    set_default_plot_size(30cm, 15cm)

    p = Gadfly.plot(
        spk_df,
        x = :name,
        y = :count,
        color = :org,
        Geom.bar
    )
    return p
end

# Plot recorded time
# ------------------------------------------------------------------------------------------------------------------

@doc """
Converts minutes exceeding 60 -> Hours and seconds exceeding 60 -> minutes
Input : t --time in Minute or seconds
Outputs : tuple (HH,MM,SS)
"""->
function convert_time(t::Union{Minute, Second})
    if typeof(t) == Second
        x, seconds = divrem(t.value, 60)
        hours, minutes = divrem(x, 60)
        return hours, minutes, seconds
    else
        hours, minutes = divrem(t.value, 60)
        return hours, minutes, 0
    end
end

function plot_recorded_time(df::DataFrame)
    # Cumulative Recorditime
    cum_sum_secs = cumsum(df.duration_secs)
    mins_from_secs = map(x -> x[2], convert_time.(cum_sum_secs)) 
    secs_from_secs = map(x -> x[3], convert_time.(cum_sum_secs)) .|> Second
    cum_sum_mins = cumsum(df.duration_mins) .+ Minute.(mins_from_secs)
    hrs_from_mins  = map(x -> x[1], convert_time.(cum_sum_mins))
    mins_from_mins = map(x -> x[2], convert_time.(cum_sum_mins)) .|> Minute
    cum_sum_hrs = cumsum(df.duration_hrs) .+ Hour.(hrs_from_mins)
    cum_total_time = cum_sum_hrs .+ mins_from_mins .+ secs_from_secs
    
    df[:, :cum_total_hrs_only] = cum_sum_hrs
    df[:, :cum_total_time] = cum_total_time

    set_default_plot_size(20cm, 15cm)

    p1 = Gadfly.plot(
        x = df.date,
        y = map(x -> x.value, df.cum_total_hrs_only),
        Geom.line,
        Theme(line_width = 0.5mm, default_color = colorant"dodgerblue"),
        Guide.xlabel("Date"),
        Guide.ylabel("Recording Time (Hrs)")
    )

    # Weekly recordings
    ta = TimeArray(df.date, hcat(df.duration_hrs, df.duration_mins))
    df_weekly = collapse(ta, week, last, sum) |> DataFrame
    df_weekly[:, "duration_mins"] = df_weekly[:,"A"] .+ df_weekly[:, "B"]
    df_weekly[:, "duration_hrs"] = map(x -> floor(x.value / 60), df_weekly[:, "duration_mins"]) 

    p2 = Gadfly.plot(
        x = df_weekly.timestamp,
        y = df_weekly.duration_hrs,
        Geom.bar,
        Guide.xlabel("Date"),
        Guide.ylabel("Recording Time (Hrs)")
    )

    p = vcat(p1,p2)
    
    return p1, p2
end

# Plot Total Recorded Hours according to recording method
# -------------------------------------------------------------------------------------------------------------

@doc """ 
    Replace Recording method value based on spk2_name column and recording method value
    Inputs:
        Col1 : String
        Col2 : String

"""->
function replace_if(val1, val2)
    if val1 == "-" && val2 == "zoom"
        return "zoom-single"
    elseif val1 != "-" && val2 == "zoom"
        return "zoom-double"
    else
        return "otter"
    end
end

function plot_recording_method(df)
    df.duration_total = map(x -> x.value / 60, df.duration_mins) .+ map(x -> x.value, df.duration_hrs)
    df_by_method = combine(groupby(df, [:recording_method, :recorded_content]), :duration_total => sum)
    p1 = Gadfly.plot(
        x = df_by_method.recorded_content,
        y = df_by_method.duration_total_sum,
        color = df_by_method.recording_method,
        Geom.bar,
        Guide.ylabel("Number Hours"),
        Guide.xlabel("Content")
    )

    return p1
end

function plot_overall_progress(df)
    df.duration_total = map(x -> x.value / 60, df.duration_mins) .+ map(x -> x.value, df.duration_hrs)
    trace1 = indicator(
        value = df[:, "cum_total_time"][end].periods[1].value,
        mode = "gauge+number+delta",
        delta = attr(reference = sum(filter(x -> x.date < (now() - Day(7)), df).duration_total)),
        gauge = attr(
            axis = attr(range = [0, 300]),
            steps = [
                attr(range = [0, 100], color = "lightgray"),
                attr(range = [100, 200], color = "darkgray"),
                attr(range = [200, 300], color = "gray")
            ]
        )
    )

    p = PlotlyJS.plot(trace1)

    return p

end
end

function main()
    df = load_data("data/staff-2021-SGH - Sheet1.csv")
    selected_cols = String["date", "spk1_name", "spk1_org", "spk1_desig", "spk2_name", "spk2_org", "spk2_desig", "recording_method", "duration", "recorded_content"]
    df = clean_dataframe(df, selected_cols)

    # Obtain Candidates Plot
    p_candidates = plot_candidates(df)

    cum_time, weekly_time = plot_recorded_time(df)
    cum_time
    weekly_time

    # Replaces values
    recording_method_new = String[]
    for (i,j) in zip(df.spk2_name, df.recording_method)
        push!(recording_method_new, replace_if(i, j))
    end

    df.recording_method = recording_method_new

    # Plot 
    p_by_method = plot_recording_method(df)
    p_by_method

    # Overall Progress 
    plot_overall_progress(df)
    return p_candidates
end


# Run Script ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end


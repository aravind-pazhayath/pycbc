from pycbc.types import zeros,TimeSeries,FrequencySeries,float32,complex64,float64,complex128
from pycbc.fft import fft,ifft
from math import log,ceil,sqrt

def get_padded_frequencyseries(vec):
    if not isinstance(vec,TimeSeries):
        raise TypeError("Can only return padded frequency series from a time series")
    else:
        power = ceil(log(len(vec),2))+1
        N = 2 ** power
        n = N/2+1
        
        vec_pad = TimeSeries(zeros(N),delta_t=vec.delta_t,dtype=float32)
        vec_pad[0:len(vec)] = vec
        
        vectilde = FrequencySeries(zeros(n),delta_f=1, dtype=complex64)
        
        fft(vec_pad,vectilde)
        
        return vectilde

def get_frequencyseries(vec):
    if isinstance(vec,FrequencySeries):
        return vec
    if isinstance(vec,TimeSeries):
        N = len(vec)
        n = N/2+1    
        delta_f = 1.0 / N / vec.delta_t
        if vec.precision is 'single':
            dtype = complex64
        elif vec.precision is 'double':
            dtype = complex128
        vectilde = FrequencySeries(zeros(n),delta_f=delta_f, dtype=dtype)
        fft(vec,vectilde)
        
        return vectilde
    else:
        raise TypeError("Can only convert a TimeSeries to a FrequencySeries")
        

def sigmasq_series(htilde,psd = None,low_frequency_cutoff=None,high_frequency_cutoff=None):
    N = (len(htilde)-1) * 2 
    norm = 4.0 / (N * N * htilde.delta_f)
    moment = htilde.conj()*htilde
    kmin,kmax = get_cutoff_indices(low_frequency_cutoff,high_frequency_cutoff,htilde.delta_f,N)
    if psd is not None:
        moment /= psd
    return moment[kmin:kmax],norm

def sigmasq(htilde,psd = None,low_frequency_cutoff=None,high_frequency_cutoff=None):
    moment,norm = sigmasq_series(htilde,psd,low_frequency_cutoff,high_frequency_cutoff)
    if psd is not None:
        moment /= psd
    return moment.real().sum() * norm
    
def get_cutoff_indices(flow,fhigh,df,N):
    if flow:
        kmin = int(flow / df)
    else:
        kmin = 1
    if fhigh:
        kmax = int(fhigh / df )
    else:
        kmax = N/2 + 1
        
    return kmin,kmax
    
def matchedfilter(template,data,psd=None,low_frequency_cutoff=None,high_frequency_cutoff=None):

    # Get the Inputs in terms of htilde and stilde
    htilde = get_frequencyseries(template)
    stilde = get_frequencyseries(data)

    # Calculate the length we need for the temporary memory 
    # Check that this is a power of two?
    N = (len(htilde)-1) * 2   
    kmin,kmax = get_cutoff_indices(low_frequency_cutoff,high_frequency_cutoff,stilde.delta_f,N) 
   
    # Create workspace memory
    if data.precision is 'single':
        dtype = complex64
    elif data.precision is 'double':
        dtype = complex128
    q = zeros(N,dtype=dtype)
    qtilde = zeros(N,dtype=dtype)
   
    #Weighted Correlation
    qtilde[kmin:kmax] = htilde.conj()[kmin:kmax] * stilde[kmin:kmax]
    
    if psd is not None:
        qtilde[kmin:kmax] /= psd[kmin:kmax]

    #Inverse FFT
    ifft(qtilde,q) 

    #Calculate the Normalization
    norm = sqrt(((4.0 / (N * N * stilde.delta_f)) **2) / sigmasq(htilde,psd,low_frequency_cutoff,high_frequency_cutoff) )

    #return complex snr
    return q,norm
    
    
def match(vec1,vec2,psd=None,low_frequency_cutoff=None,high_frequency_cutoff=None):
    htilde = get_frequencyseries(vec1)
    stilde = get_frequencyseries(vec2)
    snr,norm = matchedfilter(htilde,stilde,psd,low_frequency_cutoff,high_frequency_cutoff)
    maxsnrsq = (snr.conj()*snr).real().max()
    return sqrt(maxsnrsq/sigmasq(stilde,psd,low_frequency_cutoff,high_frequency_cutoff))*norm
    
def real_same_precision_as(data):
    if data.precision is 'single':
        return float32
    elif data.precision is 'double':
        return float64
        
def complex_same_precision_as(data):
    if data.precision is 'single':
        return float64
    elif data.precision is 'double':
        return complex128
    
def chisq(template, data,num_bins, psd = None , low_frequency_cutoff=None,high_frequency_cutoff=None):
    bins = get_chisq_bin_sizes(num_bins,template,psd,low_frequency_cutoff,high_frequency_cutoff)
 
    total_snr,norm = matchedfilter(template,data,psd,low_frequency_cutoff,high_frequency_cutoff)
    
    bin_snrs = []
    N = (len(htilde)-1) * 2   
    delta_t = 1.0 / N / data.delta_f
    
    chisq_series = TimeSeries(zeros(N),delta_t=delta_t,dtype = real_same_precision_as(data))
    
    for kmin,kmax in bins:
        template_piece = template[kmin:kmax]
        snr,part_norm = matchedfilter(template_piece,data,psd,low_frequency_cutoff,high_frequency_cutoff)
        delta = (snr/num_bins - total_snr)
        chisq_series += (delta.conj()*delta).real()
        
    chisq_series *= norm * num_bins
    return chisq_series
    
   
def get_chisq_bin_sizes(num_bins,template,psd=None,low_frequency_cutoff=None,high_frequency_cutoff=None):
    pass
    
    




    

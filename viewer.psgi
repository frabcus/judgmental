#!/usr/bin/perl

use warnings;
use strict;

use feature ':5.10';

use Log::Dispatch;
use Plack::Builder;

my $app = Plack::App::IndexFile->new({ root => './public_html' })->to_app;

# For Plack::Middleware::AccessLog

my $logger = Log::Dispatch->new(
    outputs => [
        [ 'File',   min_level => 'debug', filename => 'logs/logfile.log' ],
        [ 'Screen', min_level => 'warning' ],
    ],
);

my $log_cb = sub {
    my $line = shift;

    # Exclude the 4 extra, UA-less requests when the ESI layer
    # GETs (head|header|nav|footer).html
    return if $line =~ m/"-" "-"/;

    my $level = 'debug';

    if (
        ($line =~ /HTTP\/1.1" (?:4\d\d|5\d\d) /)
        and ($line !~ /Googlebot|bingbot|baidu|ahrefs|YandexBot/)
    ) {
        $level = 'warning';
    }

    $logger->log( level => $level, message => $line );
};

# For Plack::Middleware::Rewrite (using to redirect)

my $spellitright = sub {
    my $env = shift;
    my $host = $env->{HTTP_HOST} || $env->{SERVER_NAME};
    return undef unless $host; # effective pass-through

    if ($host =~ s/judgemental\.org\.uk/judgmental\.org\.uk/) {
        my $redirect = 'http://' . $host . $env->{REQUEST_URI};

        my $message =<<"END";
The proper spelling is 'judgmental.org.uk' (no 'e' after the 'g').<br />
You should be redirected there shortly.<br />
If not, please <a href="$redirect">click here</a>.
END
        return [
            '301',
            [ Location => $redirect ],
            [ $message ],
        ];
    }

    # Didn't see the errant 'e' - continue as normal
    return undef;
};


return builder {
    enable 'Rewrite', rules => $spellitright;
    enable 'ESI';
    enable 'AccessLog', logger => $log_cb;
#    enable 'Debug';
    $app;
};

package Plack::App::IndexFile;

use parent 'Plack::App::File';

sub locate_file
{
    my ($self, $env) = @_;
    my $path         = $env->{PATH_INFO} || '';

    return $self->SUPER::locate_file( $env ) unless $path && $path !~ m{\.[[:alnum:]]{2,4}$};
    $env->{PATH_INFO} .= ( substr( $env->{PATH_INFO}, -1 ) eq '/' ? '' : '/' ) . 'index.html';
    return $self->SUPER::locate_file( $env );
}


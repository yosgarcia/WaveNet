import logging
logging.getLogger().setLevel(logging.INFO)
from dispositivo_wavenet.dispositivo_wavenet import DispositivoWaveNet as wn

text = """
#include <bits/stdc++.h>

using namespace std;

#ifdef LOCAL
#define debug(arg) cout << "[" << #arg << "]: " << arg << endl
#else
#define debug(arg) 42
#endif

using llu = unsigned long long;
using Lf = long double;
using lld = long long;

#define vec vector
#define pb push_back
#define all(n) begin(n), end(n)

void solv() {
	int n; cin >> n;
	vec<int> a(n); for (auto &i : a) cin >> i;
	for (int i = 0; i < n; ++i) if (a[i] != a[n - i - 1]) return void(cout << "NO\\n");
	cout << "YES\\n";
}

int main() {
	ios_base::sync_with_stdio(0);
	cin.tie(0);
	int t = 1;
	cin >> t;
	while (t--) solv();
	return 0;
}

"""

def send():
	w = wn("1:1:1:1:1:1", "0:0:0:0:0:0")
	w.send(text, timeout=20)

send()

.PHONY: installdeps srpm

installdeps:
	dnf -y install git python3-devel

srpm: installdeps
	mkdir -p tmp.repos/SOURCES
	./build.sh dist
	cp *.tar.gz ./tmp.repos/SOURCES/
	rpmbuild \
		-D "_topdir tmp.repos" \
		-bs ./python-ovirt-engine-sdk4.spec
	cp tmp.repos/SRPMS/*.src.rpm $(outdir)
